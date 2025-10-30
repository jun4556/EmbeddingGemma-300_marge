# api_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pprint 
import traceback 

# ▼▼▼ 修正箇所 ▼▼▼
# main.pyから必要な全てのヘルパー関数をインポート
from main import (
    find_best_matches, 
    merge_uml_data, 
    merge_attributes_with_ai, 
    calculate_structural_similarity, 
    calculate_spatial_similarity_advanced,
    get_spatial_signature,
    compare_signatures,
    get_relations_for_class,
    parse_multiplicity,
    merge_multiplicity,
    adjust_layout_with_repulsion
)
# ▲▲▲ 修正ここまで ▲▲▲

from file_io import parse_uml_string, write_uml_string
from similarity_calculator import SimilarityCalculator

# Flaskアプリケーションを初期化
app = Flask(__name__)
CORS(app) 

# AIモデルを最初に一度だけ読み込む
print("AIモデルを読み込んでいます...")
calculator = SimilarityCalculator()
if not calculator.model:
    print("AIモデルの読み込みに失敗しました。プログラムを終了します。")
    exit()
print("AIモデルの準備が完了しました。")


def merge_from_strings(data_a_str, data_b_str):
    """
    2つのUMLデータ文字列を受け取り、マージした結果の文字列を返す関数
    """
    try:
        # === デバッグログ 1: 入力文字列の確認 ===
        print("\n--- [Debug 1] Input Strings ---")
        print(f"DataA Length: {len(data_a_str)}")
        print(f"DataB Length: {len(data_b_str)}")
        print(f"DataA Preview:\n{data_a_str[:300]}...")
        print(f"DataB Preview:\n{data_b_str[:300]}...")
        print("-------------------------------\n")

        # 文字列からUMLデータを解析
        data_a = parse_uml_string(data_a_str)
        data_b = parse_uml_string(data_b_str)
        if not (data_a and data_b):
            print("[Error] Failed to parse one or both UML strings.")
            return None

        # === デバッグログ 2: パース結果の確認 ===
        print("\n--- [Debug 2] Parsed Data ---")
        print(f"Parsed DataA Classes ({len(data_a['classes'])}):")
        pprint.pprint([repr(c) for c in data_a['classes']])
        print(f"Parsed DataA Relations ({len(data_a['relations'])}):")
        pprint.pprint([repr(r) for r in data_a['relations']])
        print(f"\nParsed DataB Classes ({len(data_b['classes'])}):")
        pprint.pprint([repr(c) for c in data_b['classes']])
        print(f"Parsed DataB Relations ({len(data_b['relations'])}):")
        pprint.pprint([repr(r) for r in data_b['relations']])
        print("-----------------------------\n")

        # main.py のロジックを使ってマージ処理を実行
        matches, unmatched_a, unmatched_b, all_scores = find_best_matches(data_a, data_b, calculator)

        # === デバッグログ 3: マッチング結果の確認 ===
        print("\n--- [Debug 3] Matching Results ---")
        print(f"Number of Matches: {len(matches)}")
        print(f"Number of Unmatched A: {len(unmatched_a)}")
        print(f"Number of Unmatched B: {len(unmatched_b)}")
        print("Matches (Top 5):")
        pprint.pprint([(f"{score:.4f}", repr(cls_a), repr(cls_b)) for score, _, _, _, _, cls_a, cls_b in matches[:5]])
        print("----------------------------------\n")

        merged_data = merge_uml_data(matches, unmatched_a, unmatched_b, data_a, data_b, calculator)

        # === デバッグログ 4: マージデータ構造の確認 ===
        print("\n--- [Debug 4] Merged Data Structure ---")
        print(f"Merged Classes ({len(merged_data['classes'])}):")
        pprint.pprint([repr(c) for c in merged_data['classes']])
        print(f"\nMerged Relations ({len(merged_data['relations'])}):")
        pprint.pprint([repr(r) for r in merged_data['relations']])
        print("---------------------------------------\n")

        # マージ結果を文字列に変換
        final_output_string = write_uml_string(merged_data)

        # === デバッグログ 5: 最終出力文字列の確認 (修正版) ===
        print("\n--- [Debug 5] Final Output String ---")
        print(f"Output String Length: {len(final_output_string)}")
        print(f"Output String Preview:\n{final_output_string[:300]}...")
        
        last_element = ""
        clean_output = final_output_string.strip()
        if clean_output:
            elements = [e for e in clean_output.split(';') if e] 
            if elements:
                last_element = elements[-1] + ';' 

        if not last_element:
             print("[Debug 5 Check] ERROR: Output string seems empty or malformed.")
        elif "Class$" in last_element and "%" in last_element:
            is_correct = last_element.endswith('%!;')
            print(f"[Debug 5 Check] Last element is a Class w/ Attributes. Ends with '%!;': {is_correct}")
        elif "Class$" in last_element:
            is_correct = last_element.endswith('!!!;')
            print(f"[Debug 5 Check] Last element is a Class w/o Attributes. Ends with '!!!;': {is_correct}")
        elif "ClassRelationLink" in last_element:
            is_correct = last_element.endswith('!!;')
            print(f"[Debug 5 Check] Last element is a Relation. Ends with '!!;': {is_correct}")
        else:
            print(f"[Debug 5 Check] Last element is unrecognized: {last_element}")
        
        print("-------------------------------------\n")

        return final_output_string

    except Exception as e:
        print(f"\n!!! Error in merge_from_strings: {e} !!!\n")
        traceback.print_exc()
        return None

@app.route('/merge', methods=['POST'])
def merge_endpoint():
    """
    /merge エンドポイント。JSONで2つのUMLデータを受け取り、マージ結果を返す
    """
    try:
        data = request.json
        data_a_str = data.get('dataA')
        data_b_str = data.get('dataB')

        print("\n--- [Python Server] Request Received ---")
        print(f"DataA Length: {len(data_a_str) if data_a_str else 0}")
        print(f"DataB Length: {len(data_b_str) if data_b_str else 0}")
        print("----------------------------------------\n")

        if not data_a_str or not data_b_str:
            return jsonify({"error": "dataA and dataB are required"}), 400

        merged_result_str = merge_from_strings(data_a_str, data_b_str)

        print("\n--- [Python Server] Response Sending ---")
        if merged_result_str:
            print(f"Merged Result Length: {len(merged_result_str)}")
            print("----------------------------------------\n")
            return merged_result_str, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            print("Merge failed, sending error response.")
            print("----------------------------------------\n")
            return jsonify({"error": "Failed to merge UML data (check Python server logs)"}), 500

    except Exception as e:
        print(f"Error in merge_endpoint: {e}!")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)