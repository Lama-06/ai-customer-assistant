# AI Customer Assistant

An AI-powered assistant that answers customer questions using verified support
documents only — combining a data quality gate, semantic search, and
Retrieval-Augmented Generation (RAG).

## Why This System?

Most chatbots either rely purely on a language model's general knowledge (which
can produce confident but wrong answers), or they skip validating their input
data entirely. This project addresses both issues: no document enters the
knowledge base unless it passes a set of quality checks, and no answer is
generated unless it is grounded in retrieved, verified content.

## How It Works

```
Raw Support Documents
        |
        v
Data Quality Gate  --(rejected)--> data/quarantine
        |
        v
Text Chunking
        |
        v
Embedding Generation (Sentence Transformers)
        |
        v
ChromaDB (persistent vector storage)
        |
        v
Semantic Retrieval  <-- user question
        |
        v
LLM Answer Generation (OpenRouter)  --> Answer + Cited Source(s)
```

## Data Quality Gate

Before any document is indexed, it must pass four checks:

| Check | What it catches |
|---|---|
| File type | Only `.txt` and `.pdf` are accepted |
| Empty file | Zero-byte files are rejected |
| Minimum content length | Files with near-empty content are rejected |
| Duplicate detection (SHA-256) | Identical content uploaded twice is caught |

Anything that fails is copied automatically into `data/quarantine/`, and a
summary report is printed showing exactly how many files passed and why the
rest were rejected.

## Tech Stack

- **Python**
- **ChromaDB** — persistent vector database
- **Sentence Transformers** (`all-MiniLM-L6-v2`) — embedding model
- **pypdf** — PDF text extraction
- **SHA-256** — duplicate detection
- **OpenRouter + OpenAI SDK** — LLM answer generation

## Project Structure

```
ai-customer-assistant/
├── app/
│   ├── config.py            # Central settings (paths, model names, thresholds)
│   ├── quality_pipeline.py  # Data quality gate
│   ├── chunking.py          # Splits documents into smaller text chunks
│   ├── vector_store.py      # ChromaDB + embeddings wrapper
│   ├── indexer.py           # Orchestrates quality -> chunking -> storage
│   ├── rag.py                # Retrieval + LLM answer generation
│   └── main.py               # CLI entry point
├── data/
│   ├── raw/                  # Source support documents (.txt / .pdf)
│   ├── quarantine/           # Auto-generated: rejected files land here
│   └── chroma_db/            # Auto-generated: persistent vector database
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup & Usage

**1. Install dependencies**
```
pip install -r requirements.txt
```

**2. Add your OpenRouter API key**

Copy `.env.example` to `.env` and fill in your key:
```
OPENROUTER_API_KEY=YOUR_API_KEY_HERE
```
The `.env` file is git-ignored and should never be pushed to GitHub.

**3. (Optional) Review the data quality report**
```
python app/quality_pipeline.py
```

**4. Run the assistant**
```
python app/main.py
```
The knowledge base is built automatically on first run. Try asking:
`How long do I have to return a product?`

## Known Limitations

- Retrieval quality depends on how closely the customer's wording matches the
  source documents — very indirect phrasing can occasionally retrieve a less
  relevant chunk.
- The system currently supports English-language documents only.

## Course

This project was made for **"Modern Data Engineering for AI Systems"** course provided by [SDAIA Academy](https://github.com/SDAIAAcademy).

## Author

Lama Alrayes
