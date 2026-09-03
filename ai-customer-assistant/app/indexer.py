"""
app/indexer.py
===================
يجمع بين ثلاث خطوات في تسلسل واحد:
  1. فحص جودة الملفات (quality_pipeline)
  2. تقطيع النصوص (chunking)
  3. تخزينها كمتجهات في ChromaDB (vector_store)

هذا الملف هو "المنسّق" (Orchestrator) لعملية بناء قاعدة المعرفة.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app import config
from app.quality_pipeline import run_quality_pipeline, read_text_content
from app.chunking import chunk_document
from app.vector_store import VectorStore


def build_knowledge_base() -> VectorStore:
    """يبني قاعدة المعرفة كاملة من الملفات الخام، ويرجع VectorStore جاهز للاستخدام."""

    print("=" * 55)
    print("الخطوة 1: فحص جودة البيانات")
    print("=" * 55)
    valid_files = run_quality_pipeline()

    print("\n" + "=" * 55)
    print("الخطوة 2 و 3: التقطيع + التحويل لمتجهات + التخزين")
    print("=" * 55)
    store = VectorStore()

    total_chunks = 0
    for file_path in valid_files:
        content = read_text_content(file_path)
        chunks = chunk_document(file_path, content, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        store.add_chunks(chunks)
        total_chunks += len(chunks)
        print(f"  {file_path.name}  →  {len(chunks)} قطعة نصية")

    print(f"\nإجمالي القطع المفهرسة في ChromaDB: {store.count()}")
    return store


if __name__ == "__main__":
    build_knowledge_base()
