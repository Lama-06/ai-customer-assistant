"""
app/quality_pipeline.py
============================
بوابة جودة البيانات (Data Quality Gate).

قبل أن يُسمح لأي مستند بالدخول إلى قاعدة المعرفة (Vector Database)،
يجب أن يجتاز أربعة فحوصات:

  1. نوع الملف صحيح (Valid File Type)      → .txt أو .pdf فقط
  2. الملف ليس فارغًا (Empty File Check)
  3. المحتوى لا يقل عن حد أدنى من الأحرف (Minimum Content Length)
  4. الملف ليس مكررًا (Duplicate Detection) → عبر بصمة SHA-256

أي ملف يفشل في أحد هذه الفحوصات يُنقل تلقائيًا إلى data/quarantine
بدلًا من فهرسته، مع تسجيل السبب.

التشغيل:
    python app/quality_pipeline.py
"""

import hashlib
import shutil
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app import config


def compute_file_hash(file_path: Path) -> str:
    """يحسب بصمة SHA-256 لمحتوى الملف، تُستخدم لاكتشاف التكرار."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_text_content(file_path: Path) -> str:
    """يقرأ محتوى الملف كنص، سواء كان .txt أو .pdf."""
    if file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if file_path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    return ""


def validate_file(file_path: Path, seen_hashes: set) -> tuple[bool, str]:
    """
    يشغّل كل فحوصات الجودة على ملف واحد.
    يرجع (True, "") لو الملف سليم، أو (False, "سبب الرفض") لو فشل.
    """
    # 1) نوع الملف
    if file_path.suffix.lower() not in config.ALLOWED_EXTENSIONS:
        return False, f"unsupported_file_type ({file_path.suffix})"

    # 2) الملف ليس فارغًا فعليًا (حجم الملف صفر)
    if file_path.stat().st_size == 0:
        return False, "empty_file"

    # 3) المحتوى لا يقل عن الحد الأدنى
    content = read_text_content(file_path)
    if len(content.strip()) < config.MIN_CONTENT_LENGTH:
        return False, f"content_too_short (<{config.MIN_CONTENT_LENGTH} chars)"

    # 4) ليس مكررًا
    file_hash = compute_file_hash(file_path)
    if file_hash in seen_hashes:
        return False, "duplicate_file"
    seen_hashes.add(file_hash)

    return True, ""


def run_quality_pipeline() -> list[Path]:
    """
    يفحص كل الملفات داخل data/raw، ينقل الفاشل منها إلى data/quarantine،
    ويرجع قائمة بمسارات الملفات السليمة الجاهزة للفهرسة.
    """
    config.QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    seen_hashes: set[str] = set()
    valid_files: list[Path] = []
    report = {"total": 0, "passed": 0, "quarantined": 0}

    for file_path in sorted(config.RAW_DATA_DIR.iterdir()):
        if file_path.is_dir():
            continue

        report["total"] += 1
        is_valid, reason = validate_file(file_path, seen_hashes)

        if is_valid:
            valid_files.append(file_path)
            report["passed"] += 1
            print(f"  ✓ {file_path.name}")
        else:
            destination = config.QUARANTINE_DIR / file_path.name
            shutil.copy(file_path, destination)
            report["quarantined"] += 1
            print(f"  ✗ {file_path.name}  →  عُزل ({reason})")

    print("\n--- تقرير جودة البيانات ---")
    print(f"  إجمالي الملفات   : {report['total']}")
    print(f"  اجتازت الفحص     : {report['passed']}")
    print(f"  عُزلت (Quarantine): {report['quarantined']}")

    return valid_files


if __name__ == "__main__":
    print("تشغيل بوابة جودة البيانات...\n")
    run_quality_pipeline()
