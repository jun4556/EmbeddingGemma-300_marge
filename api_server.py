# Flaskと必要なモジュールをインポート
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

# ご提供いただいたマージプログラムの関数をインポート
# (main.pyを少し変更して、マージ処理を関数として呼び出せるようにします)
from main import find_best_matches, merge_uml_data
from file_io import parse_uml_string, write_uml_string # 文字列を直接扱うように変更
from similarity_calculator import SimilarityCalculator

# Flaskアプリケーションを初期化
app = Flask(__name__)
CORS(app) # クロスオリジンリクエストを許可

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
    # 文字列からUMLデータを解析
    data_a = parse_uml_string(data_a_str)
    data_b = parse_uml_string(data_b_str)
    if not (data_a and data_b):
        return None

    # main.py のロジックを使ってマージ処理を実行
    matches, unmatched_a, unmatched_b, _ = find_best_matches(data_a, data_b, calculator)
    merged_data = merge_uml_data(matches, unmatched_a, unmatched_b, data_a, data_b, calculator)
    
    # マージ結果を文字列に変換して返す
    return write_uml_string(merged_data)

@app.route('/merge', methods=['POST'])
def merge_endpoint():
    """
    /merge エンドポイント。JSONで2つのUMLデータを受け取り、マージ結果を返す
    """
    try:
        # リクエストからJSONデータを取得
        data = request.json
        data_a_str = data.get('dataA')
        data_b_str = data.get('dataB')
        # ▼▼▼ デバッグログ追加 (1/2) ▼▼▼
        print("--- [Python Server] Request Received ---")
        print(f"DataA Length: {len(data_a_str) if data_a_str else 0}")
        print(f"DataB Length: {len(data_b_str) if data_b_str else 0}")
        # print(f"DataA (Preview): {data_a_str[:200] if data_a_str else 'None'}")
        # print(f"DataB (Preview): {data_b_str[:200] if data_b_str else 'None'}")
        print("----------------------------------------")
        # ▲▲▲ デバッグログ追加 ▲▲▲
        if not data_a_str or not data_b_str:
            return jsonify({"error": "dataA and dataB are required"}), 400

        # マージ処理を実行
        merged_result_str = merge_from_strings(data_a_str, data_b_str)
        # ▼▼▼ デバッグログ追加 (2/2) ▼▼▼
        print("--- [Python Server] Response Sending ---")
        print(f"Merged Result Length: {len(merged_result_str) if merged_result_str else 0}")
        # print(f"Merged Result (Preview): {merged_result_str[:200] if merged_result_str else 'None'}")
        print("----------------------------------------")
        # ▲▲▲ デバッグログ追加 ▲▲▲
        if merged_result_str:
            # 成功したらマージ結果をプレーンテキストで返す
            return merged_result_str, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            return jsonify({"error": "Failed to merge UML data"}), 500

    except Exception as e:
        print(f"Error during merge: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # サーバーを起動 (ポート8000番)
    app.run(host='0.0.0.0', port=8000)