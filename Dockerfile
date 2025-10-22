# 1. ベースとなるPythonのイメージを選択
# (使用しているPythonのバージョンに合わせてください)
FROM python:3.10-slim

# 2. コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 3. 必要なライブラリをインストール
# (Flask, FastAPI, uvicorn など、サーバーが依存するライブラリ)
# まず requirements.txt だけをコピーしてインストールする
# (ソースコード変更時に毎回ライブラリをインストールし直さないため)
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. プロジェクトのソースコードをコンテナにコピー
COPY . .

# 5. サーバーが使用するポートを指定 (Java側が 8000 に接続するため)
EXPOSE 8000

# 6. コンテナ起動時に実行するコマンド
# (例: FastAPI + uvicorn の場合)
# "0.0.0.0" はコンテナ外部からのアクセスを許可するために必要です
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# (例: 単純なFlaskの場合)
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
# (※Flaskの場合は環境変数 FLASK_APP=app.py が必要かもしれません)