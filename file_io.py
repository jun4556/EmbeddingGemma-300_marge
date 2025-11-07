# file_io.py (修正版)

import re
from uml_data import UmlClass, UmlRelation

def parse_uml_string(uml_content):
    """UMLデータ文字列を解析してクラスと関連のリストを返す（スタイル情報対応版）"""
    classes = []
    relations = []

    class_pattern = re.compile(r"<(\d+)>]Class\$\((\d+),(\d+)\)!([^!]*)!(.*)")
    
    # ▼▼▼ 正規表現パターンをスタイル情報（LineStyle, SourceArrow, TargetArrow）を
    #      キャプチャできるように修正 ▼▼▼
    relation_pattern = re.compile(
        r"<(\d+)>]ClassRelationLink\$<(\d+)>!<(\d+)>!"
        r"([^!]*)!!"  # 1: Type
        r"([^!]*)!"   # 2: LineStyle (e.g., Solid, Dashed)
        r"([^!]*)!"   # 3: SourceArrow (e.g., None, WireArrow)
        r"([^!]*)!!!" # 4: Source Multi
        r"([^!]*)!"   # 5: TargetArrow (e.g., None, SolidArrow)
        r"([^!]*)"     # 6: Target Multi (末尾の '!!;' を削除)
    )
    # ▲▲▲ 正規表現ここまで ▲▲▲

    elements = [elem.strip() for elem in uml_content.split(';') if elem.strip()]

    for element in elements:
        class_match = class_pattern.match(element)
        if class_match:
            id, x, y, name, rest = class_match.groups()
            attributes = []
            if rest.startswith('!-'):
                attrs_str = rest[2:]
                if attrs_str.endswith('%!'):
                    attrs_str = attrs_str[:-2]
                elif attrs_str.endswith('%'):
                     attrs_str = attrs_str[:-1]
                raw_attributes = attrs_str.split('%-')
                attributes = [attr.strip() for attr in raw_attributes if attr.strip()]
            classes.append(UmlClass(id, name, attributes, int(x), int(y)))
            continue

        relation_match = relation_pattern.match(element)
        if relation_match:
            # ▼▼▼ キャプチャしたグループを新しいUmlRelationの引数に渡す ▼▼▼
            try:
                (id, source_id, target_id, 
                 rel_type, 
                 line_style, source_arrow, source_multi, 
                 target_arrow, target_multi) = relation_match.groups()
                
                relations.append(UmlRelation(
                    id, source_id, target_id, 
                    rel_type, source_multi, target_multi,
                    line_style, source_arrow, target_arrow # スタイル情報を渡す
                ))
            except ValueError:
                print(f"[Warning] Failed to parse relation groups: {element}")
            # ▲▲▲ 変更ここまで ▲▲▲
            continue

    return {"classes": classes, "relations": relations}


def write_uml_string(uml_data):
    """UMLデータを文字列形式で書き出す（スタイル情報対応版）"""
    lines = []

    for uml_class in uml_data["classes"]:
        if uml_class.attributes:
            attrs_str = "%-".join(uml_class.attributes)
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!-{attrs_str}%!;"
        else:
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!!;"
        lines.append(line)

    for rel in uml_data["relations"]:
        rel_type = rel.type if rel.type else 'SimpleRelation'
        source_multi = rel.source_multiplicity if rel.source_multiplicity else 'None'
        target_multi = rel.target_multiplicity if rel.target_multiplicity else 'None'

        # ▼▼▼ ハードコーディングされていたスタイルを削除 ▼▼▼
        #     relオブジェクトから保存されているスタイル情報を取得する
        line_style = rel.line_style if rel.line_style else "Solid"
        source_arrow = rel.source_arrow if rel.source_arrow else "None"
        target_arrow = rel.target_arrow if rel.target_arrow else "None"
        
        # (型に基づく強制的な矢印の上書きロジックは削除し、
        #  読み込まれたスタイルをそのまま書き出すように変更)
        # ▲▲▲ 変更ここまで ▲▲▲

        style_part = f"{line_style}!{source_arrow}"
        line = (f"<{rel.id}>]ClassRelationLink$<{rel.source_id}>!<"
                f"{rel.target_id}>!{rel_type}!!{style_part}!{source_multi}!!!"
                f"{target_arrow}!{target_multi}!!;")
        lines.append(line)

    return "".join(lines)