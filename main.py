# main.py
import math
import re
from file_io import parse_uml_string, write_uml_string
from similarity_calculator import SimilarityCalculator
from uml_data import UmlClass, UmlRelation

def get_relations_for_class(class_id, relations):
    related = {"source": [], "target": []}
    for rel in relations:
        if rel.source_id == class_id:
            related["source"].append(rel)
        if rel.target_id == class_id:
            related["target"].append(rel)
    return related

def calculate_structural_similarity(cls_a, cls_b, data_a, data_b):
    relations_a = get_relations_for_class(cls_a.id, data_a["relations"])
    relations_b = get_relations_for_class(cls_b.id, data_b["relations"])
    source_count_a = len(relations_a["source"])
    source_count_b = len(relations_b["source"])
    target_count_a = len(relations_a["target"])
    target_count_b = len(relations_b["target"])
    source_diff = abs(source_count_a - source_count_b) / max(1, source_count_a + source_count_b)
    target_diff = abs(target_count_a - target_count_b) / max(1, target_count_a + target_count_b)
    similarity = 1.0 - (source_diff + target_diff) / 2
    return similarity

def get_spatial_signature(cls, diagram_data):
    signature = []
    class_map = {c.id: c for c in diagram_data["classes"]}
    for rel in diagram_data["relations"]:
        neighbor_cls = None
        if rel.source_id == cls.id and rel.target_id in class_map:
            neighbor_cls = class_map[rel.target_id]
        elif rel.target_id == cls.id and rel.source_id in class_map:
            neighbor_cls = class_map[rel.source_id]
        if neighbor_cls:
            relative_vector = (neighbor_cls.x - cls.x, neighbor_cls.y - cls.y)
            signature.append(relative_vector)
    signature.sort()
    return signature

def compare_signatures(sig_a, sig_b):
    if not sig_a and not sig_b: return 1.0
    if not sig_a or not sig_b: return 0.0
    def vector_distance(v1, v2):
        return math.sqrt((v1[0] - v2[0])**2 + (v1[1] - v2[1])**2)
    total_distance = 0
    matched_b_indices = set()
    for vec_a in sig_a:
        min_dist = float('inf')
        best_match_idx = -1
        for i, vec_b in enumerate(sig_b):
            if i in matched_b_indices: continue
            dist = vector_distance(vec_a, vec_b)
            if dist < min_dist:
                min_dist = dist
                best_match_idx = i
        if best_match_idx != -1:
            total_distance += min_dist
            matched_b_indices.add(best_match_idx)
    avg_distance = total_distance / len(sig_a) if sig_a else 0
    similarity = 1 / (1 + avg_distance / 100)
    len_diff_penalty = 1.0 - (abs(len(sig_a) - len(sig_b)) / max(len(sig_a), len(sig_b)))
    return similarity * len_diff_penalty

def calculate_spatial_similarity_advanced(cls_a, data_a, cls_b, data_b):
    signature_a = get_spatial_signature(cls_a, data_a)
    signature_b = get_spatial_signature(cls_b, data_b)
    
    # A->B と B->A の両方を計算し、平均を取る (対称性を確保)
    score_ab = compare_signatures(signature_a, signature_b)
    score_ba = compare_signatures(signature_b, signature_a)
    
    symmetric_score = (score_ab + score_ba) / 2.0
    return symmetric_score

def find_best_matches(data_a, data_b, calculator, threshold=0.6, weights=None):
    if weights is None:
        weights = {"semantic": 0.7, "relational": 0.0, "structural": 0.15, "spatial": 0.15}
    classes_a, classes_b = list(data_a["classes"]), list(data_b["classes"])
    all_scores = []
    for cls_a in classes_a:
        for cls_b in classes_b:
            text_a = f"{cls_a.name} {' '.join(cls_a.attributes)}"
            text_b = f"{cls_b.name} {' '.join(cls_b.attributes)}"
            semantic_score = calculator.get_similarity(text_a, text_b)
            structural_score = calculate_structural_similarity(cls_a, cls_b, data_a, data_b)
            spatial_score = calculate_spatial_similarity_advanced(cls_a, data_a, cls_b, data_b)
            total_score = (semantic_score * weights["semantic"] +
                           structural_score * weights["structural"] +
                           spatial_score * weights["spatial"])
            all_scores.append((total_score, semantic_score, 0.0, structural_score, spatial_score, cls_a, cls_b))
    all_scores.sort(key=lambda x: x[0], reverse=True)
    matched_pairs, matched_a_ids, matched_b_ids = [], set(), set()
    def add_match(score_tuple):
        cls_a, cls_b = score_tuple[5], score_tuple[6]
        if cls_a.id not in matched_a_ids and cls_b.id not in matched_b_ids:
            matched_pairs.append(score_tuple)
            matched_a_ids.add(cls_a.id)
            matched_b_ids.add(cls_b.id)
    for st in all_scores:
        if st[5].name == st[6].name: add_match(st)
    for st in all_scores:
        if st[1] >= 0.95: add_match(st)
    for st in all_scores:
        if st[0] >= threshold: add_match(st)
    unmatched_a = [cls for cls in classes_a if cls.id not in matched_a_ids]
    unmatched_b = [cls for cls in classes_b if cls.id not in matched_b_ids]
    matched_pairs.sort(key=lambda x: x[0], reverse=True)
    return matched_pairs, unmatched_a, unmatched_b, all_scores

def merge_attributes_with_ai(attrs_a, attrs_b, calculator, perfect_match_threshold=0.98):
    merged_attrs, matched_b_indices = [], set()
    merged_attrs.extend(attrs_a)
    for i, attr_a in enumerate(attrs_a):
        for j, attr_b in enumerate(attrs_b):
            if j in matched_b_indices: continue
            if calculator.get_similarity(attr_a, attr_b) >= perfect_match_threshold:
                matched_b_indices.add(j)
                break
    for j, attr_b in enumerate(attrs_b):
        if j not in matched_b_indices: merged_attrs.append(attr_b)
    return sorted(list(set(merged_attrs)))

def parse_multiplicity(multi_str):
    if multi_str is None or multi_str.lower() == 'none' or not multi_str: return (1, 1)
    if multi_str == '*': return (0, float('inf'))
    if '..' in multi_str:
        low, high = multi_str.split('..')
        low = int(low) if low.isdigit() else 0
        high = float('inf') if high == '*' else int(high)
        return (low, high)
    if multi_str.isdigit():
        val = int(multi_str)
        return (val, val)
    return (1, 1)

def merge_multiplicity(multi_a, multi_b):
    low_a, high_a = parse_multiplicity(multi_a)
    low_b, high_b = parse_multiplicity(multi_b)
    merged_low, merged_high = min(low_a, low_b), max(high_a, high_b)
    if merged_low == merged_high: return str(int(merged_low))
    high_str = '*' if merged_high == float('inf') else str(int(merged_high))
    return f"{int(merged_low)}..{high_str}"

def adjust_layout_with_repulsion(classes, k_repulsion=20000, iterations=100):
    for _ in range(iterations):
        for i, cls_i in enumerate(classes):
            net_force_x, net_force_y = 0.0, 0.0
            for j, cls_j in enumerate(classes):
                if i == j: continue
                dx, dy = cls_i.x - cls_j.x, cls_i.y - cls_j.y
                distance_sq = dx**2 + dy**2
                if distance_sq < 1: distance_sq = 1
                force = k_repulsion / distance_sq
                net_force_x += force * dx / math.sqrt(distance_sq)
                net_force_y += force * dy / math.sqrt(distance_sq)
            cls_i.x += int(net_force_x / 10)
            cls_i.y += int(net_force_y / 10)
    return classes

def merge_uml_data(matches, unmatched_a, unmatched_b, data_a, data_b, calculator):
    merged_classes, id_map_a, id_map_b = [], {}, {}
    new_id_counter = 0

    # 1. クラスのマージ
    for _, _, _, _, _, cls_a, cls_b in matches:
        merged_attrs = merge_attributes_with_ai(cls_a.attributes, cls_b.attributes, calculator)
        merged_name = cls_a.name if cls_a.name == cls_b.name else f"{cls_a.name}/{cls_b.name}"
        merged_x, merged_y = (cls_a.x + cls_b.x) // 2, (cls_a.y + cls_b.y) // 2
        new_class = UmlClass(str(new_id_counter), merged_name, merged_attrs, merged_x, merged_y)
        new_id_counter += 1
        merged_classes.append(new_class)
        id_map_a[cls_a.id], id_map_b[cls_b.id] = new_class.id, new_class.id

    # マッチしなかったクラスを結合し、名前でソート (対称性の向上)
    all_unmatched = unmatched_a + unmatched_b
    all_unmatched.sort(key=lambda cls: cls.name) 

    for cls in all_unmatched:
        # A由来かB由来かを判断
        is_from_a = any(cls is c for c in data_a['classes'])
        is_from_b = any(cls is c for c in data_b['classes'])

        origin_map = None
        if is_from_a and cls.id not in id_map_a:
            origin_map = id_map_a
        elif is_from_b and cls.id not in id_map_b:
            origin_map = id_map_b
        else:
             continue

        if cls.id not in origin_map:
            new_class = UmlClass(str(new_id_counter), cls.name, cls.attributes, cls.x, cls.y)
            new_id_counter += 1
            merged_classes.append(new_class)
            origin_map[cls.id] = new_class.id

    # 2. 関連のマージ
    potential_relations = {}
    relation_priority = {'Composition': 4, 'Aggregation': 3, 'Generalization': 2, 'SimpleRelation': 1}
    all_relations = data_a["relations"] + data_b["relations"]

    for rel in all_relations:
        # 関連の出自を判断
        is_from_a = any(rel is r for r in data_a['relations'])
        is_from_b = any(rel is r for r in data_b['relations'])

        origin_map = None
        if is_from_a:
            origin_map = id_map_a
        elif is_from_b:
            origin_map = id_map_b
        else:
            continue

        new_source_id = origin_map.get(rel.source_id)
        new_target_id = origin_map.get(rel.target_id)

        if not (new_source_id and new_target_id):
            continue

        rel_key = tuple(sorted((new_source_id, new_target_id)))
        current_priority = relation_priority.get(rel.type, 0)

        if rel_key not in potential_relations or current_priority > relation_priority.get(potential_relations[rel_key].type, 0):
            potential_relations[rel_key] = UmlRelation("temp_id", new_source_id, new_target_id, rel.type, rel.source_multiplicity, rel.target_multiplicity)
        elif current_priority == relation_priority.get(potential_relations[rel_key].type, 0):
            existing_rel = potential_relations[rel_key]
            if existing_rel.type == rel.type:
                existing_rel.source_multiplicity = merge_multiplicity(existing_rel.source_multiplicity, rel.source_multiplicity)
                existing_rel.target_multiplicity = merge_multiplicity(existing_rel.target_multiplicity, rel.target_multiplicity)

    # IDを再割り当て
    merged_relations = []
    sorted_potential_relations = sorted(potential_relations.values(), key=lambda r: (r.source_id, r.target_id))
    for rel in sorted_potential_relations:
        rel.id = str(new_id_counter)
        new_id_counter += 1
        merged_relations.append(rel)

    merged_classes = adjust_layout_with_repulsion(merged_classes)
    merged_classes.sort(key=lambda c: int(c.id))
    return {"classes": merged_classes, "relations": merged_relations}

def main():
    def read_file_content(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"エラー: テスト用のファイル '{file_path}' が見つかりません。")
            return None
    data_a_content = read_file_content("dataA.txt")
    data_b_content = read_file_content("dataB.txt")
    if not (data_a_content and data_b_content): return
    data_a = parse_uml_string(data_a_content)
    data_b = parse_uml_string(data_b_content)
    if not (data_a and data_b): return
    calculator = SimilarityCalculator()
    if not calculator.model: return
    matches, unmatched_a, unmatched_b, all_scores = find_best_matches(data_a, data_b, calculator)
    print("\n--- 全てのクラスペアの類似度スコア一覧 ---")
    print(f"{'Total':<8}{'Semantic':<10}{'Structural':<12}{'Spatial':<10}{'Class A':<25}{'Class B':<25}")
    print("-" * 85)
    for score, sem, _, stru, spa, cls_a, cls_b in all_scores:
        print(f"{score:<8.4f}{sem:<10.4f}{stru:<12.4f}{spa:<10.4f}{cls_a.name:<25}{cls_b.name:<25}")
    print("\n" + "="*40)
    print("--- マージ処理を実行中... ---")
    merged_data = merge_uml_data(matches, unmatched_a, unmatched_b, data_a, data_b, calculator)
    merged_content = write_uml_string(merged_data)
    output_filename = "data_merged.txt"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    print(f"マージが完了し、'{output_filename}' に結果を保存しました。")

if __name__ == "__main__":
    main()