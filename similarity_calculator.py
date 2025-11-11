# similarity_calculator.py (300mモデル版)

from sentence_transformers import SentenceTransformer, util

class SimilarityCalculator:
    """SentenceTransformerを使ってテキストの類似度を計算するクラス"""

    # ここのモデル名を'google/embeddinggemma-300m'に変更します
    def __init__(self, model_name='google/embeddinggemma-300m'):
        """
        コンストラクタ。指定されたモデルを読み込みます。
        初回実行時はモデルのダウンロードに時間がかかる場合があります。
        """
        print(f"'{model_name}' モデルを読み込んでいます...")
        try:
            self.model = SentenceTransformer(model_name)
            print("モデルの読み込みが完了しました。")
        except Exception as e:
            print(f"モデル読み込み中にエラーが発生しました: {e}")
            print("Hugging Faceへのログインが完了しているか、モデルページで利用規約に同意しているか確認してください。")
            self.model = None

    def get_similarity(self, text1, text2):
        """
        2つのテキストのコサイン類似度を計算します。
        """
        if not self.model:
            return 0.0
        
        # ▼▼▼ 修正箇所 ▼▼▼
        # ドキュメント に基づき、タスクとして "STS" (Semantic Textual Similarity) を指定する
        # これにより、「意味が似ている」ではなく「同義語か」を判断させる
        try:
            embeddings = self.model.encode(
                [text1, text2],
                prompt_name="STS"  # タスクを指定
            )
        except Exception as e:
            # (HuggingFaceのライブラリが古い場合、prompt_name引数がない可能性があるため)
            print(f"[Warning] prompt_name='STS' の使用に失敗しました。デフォルト動作に戻します。エラー: {e}")
            embeddings = self.model.encode([text1, text2])
        # ▲▲▲ 修正ここまで ▲▲▲
        
        score = util.cos_sim(embeddings[0], embeddings[1])[0][0]
        
        return score.item()