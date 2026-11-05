# QA System

A local retrieval-augmented question-answering app for the PDF reports in this folder.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. The app reads every `.pdf` in the same folder, extracts text page by page, builds overlapping chunks, retrieves passages with TF-IDF, and displays answer evidence with source pages.

## Chunk-size recommendation

The default is **700 words with 100 words of overlap**. It is a practical starting point for report-style PDFs: enough context for an answer while retaining passage-level retrieval precision. The UI exposes the setting so it can be compared against the corpus statistics.

Use 400-500 words for narrow fact lookup and 900-1,200 words for questions that depend on broader context. If the PDFs are scanned images and contain little or no extractable text, OCR is needed before indexing.

## Architecture

- `rag_system.py`: PDF extraction, page metadata, standard-library TF-IDF retrieval, extractive answer synthesis, and corpus metrics.
- `app.py`: Streamlit interface and adjustable chunking controls.
- The system is intentionally local and does not require an API key or send document content to a third party.
