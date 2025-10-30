# 推奨コマンド

## 環境セットアップ
```bash
# 依存関係のインストール
pip install -r requirements.txt
```

## アプリケーションの実行
```bash
# APIサーバーの起動
python api_server.py

# ファイルからのマージ処理実行
python main.py
```

## 開発用コマンド
```bash
# Gitコマンド
git status  # 変更状態の確認
git add .   # 変更のステージング
git commit -m "コミットメッセージ"  # 変更のコミット
git push    # リモートリポジトリへのプッシュ

# ファイル操作（Windows）
dir         # ディレクトリ内容の表示
type        # ファイル内容の表示（Unix の cat に相当）
cd          # ディレクトリの移動
```

## その他の有用なコマンド
```bash
# Pythonインタープリタでのテスト実行
python -i file_name.py  # 対話モードでファイルを実行

# モジュールのバージョン確認
pip freeze  # インストール済みパッケージの一覧表示