# プロジェクト概要

このプロジェクトは、UMLクラス図のマージ機能を提供するPythonアプリケーションです。主な機能として：

1. 2つのUMLクラス図のデータを比較・マージする機能
2. クラス間の構造的・空間的類似度の計算
3. AIを活用した属性のマージ
4. マージ結果のAPIエンドポイントを提供

## 技術スタック

- Python 3.11
- Flask (APIサーバー)
- sentence-transformers (テキスト類似度計算)
- その他の主要なライブラリ:
  - numpy
  - scikit-learn
  - transformers
  - networkx (グラフ処理)

## アプリケーション構成

主要なファイル：
- `api_server.py`: Flask APIサーバー
- `main.py`: UMLマージのメイン処理
- `similarity_calculator.py`: 類似度計算機能
- `file_io.py`: ファイル入出力処理
- `uml_data.py`: UMLデータ構造定義