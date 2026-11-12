from pathlib import Path

import streamlit as st

from rag_system import LocalRAG, format_source

BASE_DIR = Path(__file__).parent

st.set_page_config(page_title="QA System", page_icon="Q", layout="wide")
st.title("QA System")
st.caption("Search six reports with page-level citations")

with st.sidebar:
    st.header("Index settings")
    chunk_size = st.slider("Chunk size (words)", 300, 1200, 700, 50)
    overlap = st.slider("Overlap (words)", 0, 250, 100, 25)
    top_k = st.slider("Retrieved passages", 1, 8, 5)
    st.caption("Changing chunk settings rebuilds the local index.")

if overlap >= chunk_size:
    st.error("Overlap must be smaller than the chunk size.")
    st.stop()

@st.cache_resource(show_spinner="Reading PDFs and building the index...")
def load_rag(selected_chunk_size: int, selected_overlap: int) -> LocalRAG:
    return LocalRAG(BASE_DIR, selected_chunk_size, selected_overlap)

rag = load_rag(chunk_size, overlap)
stats = rag.stats

metric_columns = st.columns(5)
metric_columns[0].metric("PDFs", stats.files)
metric_columns[1].metric("Pages", stats.pages)
metric_columns[2].metric("Words", f"{stats.words:,}")
metric_columns[3].metric("Chunks", f"{stats.chunks:,}")
metric_columns[4].metric("Avg words/page", f"{stats.average_words_per_page:,.0f}")

query = st.text_area(
    "Ask a question",
    placeholder="How are AI coding tools changing software engineering teams?",
    height=90,
)

if st.button("Answer", type="primary", disabled=not query.strip()):
    answer, results = rag.answer(query, top_k=top_k)
    st.subheader("Answer")
    st.write(answer)

    if results:
        st.subheader("Sources")
        for result in results:
            with st.expander(
                f"{format_source(result)} | relevance {result.score:.3f}"
            ):
                st.write(result.chunk.text)

st.divider()
st.subheader("Corpus and chunking guidance")
st.write(
    f"The indexed corpus contains {stats.words:,} extracted words across "
    f"{stats.pages:,} pages. The current {chunk_size}-word setting creates "
    f"{stats.chunks:,} chunks with {overlap} words of overlap. "
    f"The median page contains {stats.median_words_per_page:,.0f} words."
)
st.info(
    "Recommended starting point: 700 words with 100-word overlap. "
    "This is large enough to preserve report context while keeping retrieval focused. "
    "For short fact lookups, try 400-500 words; for multi-page analysis, try 900-1,200 words."
)
