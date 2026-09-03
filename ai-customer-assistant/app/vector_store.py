"""
app/vector_store.py
========================
غلاف (Wrapper) بسيط حول ChromaDB، مسؤول عن:
  - تحويل النصوص لمتجهات (Embeddings) عبر Sentence Transformers
  - تخزين المتجهات في قاعدة بيانات دائمة (Persistent) على القرص
  - البحث الدلالي (Semantic Search) عن أقرب القطع لسؤال المستخدم
"""

import chromadb
from sentence_transformers import SentenceTransformer

from app import config


class VectorStore:
    def __init__(self):
        # نموذج تحويل النص إلى متجه رقمي (يُحمَّل من الإنترنت أول مرة فقط،
        # ثم يُخزَّن محليًا على جهازك ويُعاد استخدامه بدون اتصال)
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

        # عميل ChromaDB دائم — البيانات تُحفظ فعليًا على القرص داخل
        # data/chroma_db ولا تُفقد بعد إغلاق البرنامج
        self.client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME
        )

    def add_chunks(self, chunks: list[dict]) -> None:
        """يحوّل قائمة قطع نصية لمتجهات ويخزّنها في ChromaDB."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [{"source": c["source"]} for c in chunks]

        embeddings = self.embedding_model.encode(texts).tolist()

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def search(self, query: str, top_k: int = None) -> list[dict]:
        """يبحث عن أقرب top_k قطع نصية لسؤال المستخدم دلاليًا."""
        top_k = top_k or config.TOP_K_RESULTS
        query_embedding = self.embedding_model.encode([query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )

        matches = []
        for i in range(len(results["documents"][0])):
            matches.append({
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "distance": results["distances"][0][i],
            })
        return matches

    def count(self) -> int:
        """عدد القطع النصية المخزّنة حاليًا في قاعدة البيانات."""
        return self.collection.count()
