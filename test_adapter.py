# test_adapter.py

from functools import lru_cache
from pathlib import Path

from rag_system import LocalRAG


BASE_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def get_rag() -> LocalRAG:
    """
    Build the RAG index once and reuse it for all tests.
    """
    return LocalRAG(
        BASE_DIR,
        chunk_size=900,
        overlap=150,
    )


def retrieve(question: str, top_k: int = 5):
    """
    Test only the retrieval component of the RAG system.
    """

    if not isinstance(question, str):
        raise TypeError("Question must be a string.")

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    rag = get_rag()

    return rag.search(
        question,
        top_k=top_k
    )


def ask_chatbot(question: str, top_k: int = 5) -> str:
    """
    Run the complete RAG pipeline:
    retrieval + answer generation.
    """

    results = retrieve(
        question,
        top_k=top_k
    )

    if not results:
        return "I could not find a relevant passage in the indexed documents."

    answer, _ = get_rag().answer(question, top_k=top_k)
    return answer


if __name__ == "__main__":
    question = "How are AI coding tools changing software engineering teams?"
    results = retrieve(question, top_k=3)
    answer = ask_chatbot(question, top_k=3)

    print(f"Retrieved passages: {len(results)}")
    print(f"Question: {question}")
    print(f"Answer: {answer[:1000]}")