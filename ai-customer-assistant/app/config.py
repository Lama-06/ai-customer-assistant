"""
app/config.py
=================
كل الإعدادات الثابتة للمشروع في مكان واحد، حتى لا تتكرر المسارات
والقيم داخل باقي الملفات.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # يقرأ متغيرات البيئة من ملف .env في جذر المشروع

# ===== المسارات =====
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

# ===== إعدادات فحص الجودة =====
ALLOWED_EXTENSIONS = {".txt", ".pdf"}
MIN_CONTENT_LENGTH = 30  # أقل عدد حروف يُعتبر معه الملف "غير فارغ فعليًا"

# ===== إعدادات التقطيع (Chunking) =====
CHUNK_SIZE = 500        # عدد الأحرف التقريبي لكل قطعة نص
CHUNK_OVERLAP = 50      # تداخل بسيط بين القطع لعدم قطع الجملة في منتصفها

# ===== إعدادات النموذج =====
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "customer_assistant_kb"

# ===== إعدادات OpenRouter (توليد الإجابة النهائية) =====
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL_NAME = "openai/gpt-4o-mini"  # يمكن تغييره لأي نموذج متاح على OpenRouter

TOP_K_RESULTS = 3  # عدد القطع النصية التي تُسترجع لكل سؤال
