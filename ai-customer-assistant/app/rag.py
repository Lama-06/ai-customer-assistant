"""
app/rag.py
==============
نظام RAG (Retrieval-Augmented Generation):

  1. Retrieval  → يسترجع أقرب قطع نصية من ChromaDB لسؤال العميل
  2. Augmented  → يبني "سياق" (Context) من تلك القطع
  3. Generation → يرسل السياق + السؤال لنموذج LLM عبر OpenRouter
                  ليصيغ إجابة نهائية طبيعية، مبنية على السياق فقط

الفكرة الأساسية: النموذج لا يجاوب من معرفته العامة، بل يُطلب منه
صراحة الاعتماد فقط على المعلومات المسترجعة — هذا يقلل احتمالية
الإجابات المختلقة (Hallucination).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from openai import OpenAI

from app import config
from app.vector_store import VectorStore

SYSTEM_PROMPT = """أنت مساعد دعم عملاء. أجب على سؤال العميل بالاعتماد حصريًا
على المعلومات الموجودة في "السياق" أدناه. إذا لم يحتوِ السياق على
إجابة كافية، قل بوضوح إنك لا تملك معلومة مؤكدة ولا تختلق إجابة."""


class RAGAssistant:
    def __init__(self, vector_store: VectorStore = None):
        self.store = vector_store or VectorStore()
        self.llm_client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
        )

    def answer(self, question: str) -> dict:
        # 1) الاسترجاع (Retrieval)
        matches = self.store.search(question)

        if not matches:
            return {
                "question": question,
                "answer": "لا توجد معلومات كافية في قاعدة المعرفة للإجابة على هذا السؤال.",
                "sources": [],
            }

        # 2) بناء السياق (Augmented Context)
        context = "\n\n".join(
            f"[مصدر: {m['source']}]\n{m['text']}" for m in matches
        )

        # 3) التوليد (Generation) عبر LLM
        response = self.llm_client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"السياق:\n{context}\n\nسؤال العميل: {question}"},
            ],
        )

        final_answer = response.choices[0].message.content

        return {
            "question": question,
            "answer": final_answer,
            "sources": list({m["source"] for m in matches}),
        }
