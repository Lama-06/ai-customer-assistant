"""
app/main.py
===============
نقطة التشغيل الرئيسية لنظام دعم العملاء الذكي.

التشغيل:
    python app/main.py

يفترض هذا الملف أن قاعدة المعرفة مبنية مسبقًا عبر:
    python app/quality_pipeline.py   (اختياري لمراجعة تقرير الجودة فقط)
    python app/indexer.py            (يبني قاعدة المعرفة كاملة)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.indexer import build_knowledge_base
from app.rag import RAGAssistant
from app import config


def main():
    print("جاري تجهيز قاعدة المعرفة...\n")

    # لو قاعدة البيانات فاضية، نبنيها أول مرة من data/raw
    from app.vector_store import VectorStore
    store = VectorStore()
    if store.count() == 0:
        store = build_knowledge_base()
    else:
        print(f"تم العثور على قاعدة معرفة جاهزة ({store.count()} قطعة نصية).\n")

    assistant = RAGAssistant(vector_store=store)

    print("\n" + "=" * 55)
    print("مساعد العملاء الذكي (AI Customer Assistant) — جاهز")
    print("اكتب 'exit' للخروج في أي وقت")
    print("=" * 55 + "\n")

    while True:
        question = input("سؤالك: ").strip()
        if question.lower() in {"exit", "quit", "خروج"}:
            print("مع السلامة!")
            break
        if not question:
            continue

        result = assistant.answer(question)
        print(f"\nالإجابة: {result['answer']}")
        print(f"المصادر: {', '.join(result['sources']) if result['sources'] else '—'}\n")


if __name__ == "__main__":
    main()
