"""
app/chunking.py
====================
تقسيم النصوص الطويلة إلى قطع (Chunks) أصغر قبل تحويلها لمتجهات.

ليش نحتاج التقطيع؟ نموذج الـ Embedding يعطي نتائج أدق لما يشتغل على
فقرة قصيرة ومركزة بدل مستند كامل طويل، وأيضًا يسهّل إرجاع "المصدر
الدقيق" (Source) اللي جابت منه الإجابة بدل مستند كامل.
"""

from pathlib import Path


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    يقسّم النص إلى قطع بطول chunk_size حرف تقريبًا، مع تداخل overlap
    حرف بين كل قطعة والتي تليها (حتى لا تُقطع جملة مهمة في المنتصف).
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def chunk_document(file_path: Path, content: str, chunk_size: int, overlap: int) -> list[dict]:
    """
    يحوّل مستند واحد إلى قائمة قطع، كل قطعة معها بيانات وصفية
    (اسم الملف المصدر) عشان نقدر نرجع المصدر لاحقًا عند الإجابة.
    """
    raw_chunks = chunk_text(content, chunk_size, overlap)
    return [
        {
            "id": f"{file_path.stem}_chunk_{i}",
            "text": chunk,
            "source": file_path.name,
        }
        for i, chunk in enumerate(raw_chunks)
    ]
