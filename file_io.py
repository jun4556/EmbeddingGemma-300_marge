import re
from uml_data import UmlClass, UmlRelation

def parse_uml_string(uml_content):
    """UMLデータ文字列を解析してクラスと関連のリストを返す（セミコロン分割による修正版）"""
    classes = []
    relations = []

    # ▼▼▼ 正規表現パターンを少し修正（特に末尾部分）▼▼▼
    # クラス名や属性に ';' が含まれないことを前提とする
    class_pattern = re.compile(r"<(\d+)>]Class\$\((\d+),(\d+)\)!([^!]*)!(.*)") # 末尾の ';' を削除
    relation_pattern = re.compile(
        r"<(\d+)>]ClassRelationLink\$<(\d+)>!<(\d+)>!"
        r"([^!]*)!!"  # Type
        r"[^!]*![^!]*!" # Style
        r"([^!]*)!!!" # Source Multi
        r"[^!]*!"      # Target Arrow
        r"([^!]*)"     # Target Multi (末尾の '!!;' を削除)
        # r"([^!]*)!!;" # 元のパターン
    )
    # ▲▲▲ 正規表現ここまで ▲▲▲

    # 文字列を ';' で分割し、空の要素を除去
    elements = [elem.strip() for elem in uml_content.split(';') if elem.strip()]

    # 分割された各要素に対してパターンマッチングを行う
    for element in elements:
        class_match = class_pattern.match(element)
        if class_match:
            id, x, y, name, rest = class_match.groups()
            attributes = []
            # 'rest' 部分に属性情報があるかチェック ('!-')
            if rest.startswith('!-'):
                attrs_str = rest[2:]
                # 属性末尾の '%!' を除去
                if attrs_str.endswith('%!'):
                    attrs_str = attrs_str[:-2]
                elif attrs_str.endswith('%'): # 念のため '%' だけの場合も考慮
                     attrs_str = attrs_str[:-1]

                raw_attributes = attrs_str.split('%-')
                # re.sub(...) は不要になる（末尾の記号は除去済みのため）
                attributes = [attr.strip() for attr in raw_attributes if attr.strip()]

            classes.append(UmlClass(id, name, attributes, int(x), int(y)))
            continue # クラスが見つかったら次の要素へ

        relation_match = relation_pattern.match(element)
        if relation_match:
            # 正規表現のグループインデックスに合わせて取得
            id, source_id, target_id, rel_type, source_multi, target_multi = relation_match.groups()
            relations.append(UmlRelation(id, source_id, target_id, rel_type, source_multi, target_multi))
            continue # 関連が見つかったら次の要素へ

        # どちらのパターンにもマッチしなかった場合（デバッグ用）
        # print(f"[Warning] Skipped unrecognized element: {element}")


    return {"classes": classes, "relations": relations}


def write_uml_string(uml_data):
    """UMLデータを文字列形式で書き出す"""
    lines = []

    for uml_class in uml_data["classes"]:
        if uml_class.attributes:
            attrs_str = "%-".join(uml_class.attributes)
            # 属性末尾は '%!;'
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!-{attrs_str}%!;"
        else:
            line = f"<{uml_class.id}>]Class$({uml_class.x},{uml_class.y})!{uml_class.name}!!!;"
        lines.append(line)

    for rel in uml_data["relations"]:
        rel_type = rel.type if rel.type else 'SimpleRelation'
        source_multi = rel.source_multiplicity if rel.source_multiplicity else 'None'
        target_multi = rel.target_multiplicity if rel.target_multiplicity else 'None'
        line_style = "Solid"
        source_arrow = "None"
        target_arrow = "None"
        if rel_type == "Generalization": target_arrow = "SolidArrow"
        elif rel_type == "Aggregation": target_arrow = "SolidDiamond"
        elif rel_type == "Composition": target_arrow = "InvertedSolidDiamond"
        # ▼▼▼ 他の関連タイプも必要に応じて追加 ▼▼▼
        # elif rel_type == "Realization": ...
        # elif rel_type == "Dependency": ...
        # elif "Association" in rel_type: ...

        style_part = f"{line_style}!{source_arrow}"
        # 関連の末尾は '!!;'
        line = (f"<{rel.id}>]ClassRelationLink$<{rel.source_id}>!<"
                f"{rel.target_id}>!{rel_type}!!{style_part}!{source_multi}!!!"
                f"{target_arrow}!{target_multi}!!;")
        lines.append(line)

    return "".join(lines)