from pathlib import Path

import pytest

from rag_system import LocalRAG


@pytest.fixture(scope="module")
def rag() -> LocalRAG:
    return LocalRAG(Path(__file__).resolve().parent)


def test_rag_builds_index(rag: LocalRAG) -> None:
    assert rag.stats.chunks > 0


def test_retrieval_returns_results(rag: LocalRAG) -> None:
    results = rag.search("AI software developer productivity", top_k=3)
    assert len(results) > 100


def test_top_k_is_respected(rag: LocalRAG) -> None:
    results = rag.search("software development", top_k=2)
    assert len(results) <= 2
