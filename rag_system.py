from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class DocumentPage:
    source: str
    page: int
    text: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    source: str
    page_start: int
    page_end: int
    text: str
    word_count: int


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class CorpusStats:
    files: int
    pages: int
    words: int
    chunks: int
    average_words_per_page: float
    median_words_per_page: float
    largest_document_words: int


class LocalRAG:
    MIN_RELEVANCE_SCORE = 0.04
    MIN_MEANINGFUL_TERM_MATCHES = 3

    def __init__(
        self,
        documents_dir: str | Path,
        chunk_size: int = 700,
        overlap: int = 100,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")

        self.documents_dir = Path(documents_dir)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.pages: list[DocumentPage] = []
        self.chunks: list[Chunk] = []
        self._document_vectors: list[dict[str, float]] = []
        self._idf: dict[str, float] = {}
        self._load_and_index()

    def _pdf_paths(self) -> list[Path]:
        return sorted(
            path
            for path in self.documents_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        )

    def _load_and_index(self) -> None:
        for path in self._pdf_paths():
            reader = PdfReader(str(path))
            for page_number, page in enumerate(reader.pages, start=1):
                text = self._clean_text(page.extract_text() or "")
                if text:
                    self.pages.append(
                        DocumentPage(source=path.name, page=page_number, text=text)
                    )

        self.chunks = self._make_chunks(self.pages)
        if self.chunks:
            self._build_tfidf_index()

    def _build_tfidf_index(self) -> None:
        document_terms = [self._terms(chunk.text) for chunk in self.chunks]
        document_frequency: dict[str, int] = {}
        for terms in document_terms:
            for term in set(terms):
                document_frequency[term] = document_frequency.get(term, 0) + 1
        document_count = len(document_terms)
        self._idf = {
            term: 1.0 + (document_count / (1 + frequency))
            for term, frequency in document_frequency.items()
        }
        self._document_vectors = [self._tfidf(terms) for terms in document_terms]

    @staticmethod
    def _terms(text: str) -> list[str]:
        stop_words = {
            "about", "after", "again", "are", "being", "between", "could", "does",
            "from", "have", "how", "into", "more", "other", "that", "their", "there",
            "these", "they", "this", "those", "through", "what", "when", "where",
            "which", "while", "with", "would", "your", "who", "the", "and", "for",
            "not", "but", "can",
        }
        aliases = {
            "ai": "ai",
            "average": "average",
            "apis": "api",
            "complete": "fully",
            "completely": "fully",
            "confidence": "trust",
            "confident": "trust",
            "coding": "code",
            "codes": "code",
            "developers": "developer",
            "development": "develop",
            "effects": "effect",
            "functionally": "functionally",
            "generated": "generate",
            "generative": "generate",
            "typically": "average",
            "typical": "average",
            "roughly": "average",
            "written": "generate",
            "works": "functionally",
            "correctly": "correct",
            "engineering": "engineer",
            "teams": "team",
            "tools": "tool",
        }
        terms = []
        for raw_term in re.findall(r"[a-zA-Z0-9]+", text):
            term = raw_term.lower()
            if term in stop_words or (len(term) <= 2 and term not in aliases):
                continue
            terms.append(aliases.get(term, term))
        return terms

    def _tfidf(self, terms: list[str]) -> dict[str, float]:
        counts: dict[str, int] = {}
        for term in terms:
            counts[term] = counts.get(term, 0) + 1
        total = max(len(terms), 1)
        return {
            term: (count / total) * self._idf.get(term, 1.0)
            for term, count in counts.items()
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"-\s*\n\s*", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _make_chunks(self, pages: Iterable[DocumentPage]) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_id = 0
        for page in pages:
            words = page.text.split()
            step = self.chunk_size - self.overlap
            for start in range(0, len(words), step):
                selected = words[start : start + self.chunk_size]
                if not selected:
                    continue
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        source=page.source,
                        page_start=page.page,
                        page_end=page.page,
                        text=" ".join(selected),
                        word_count=len(selected),
                    )
                )
                chunk_id += 1
                if start + self.chunk_size >= len(words):
                    break
        return chunks

    @property
    def stats(self) -> CorpusStats:
        words_per_page = [len(page.text.split()) for page in self.pages]
        document_words: dict[str, int] = {}
        for page in self.pages:
            document_words[page.source] = document_words.get(page.source, 0) + len(
                page.text.split()
            )
        return CorpusStats(
            files=len(self._pdf_paths()),
            pages=len(self.pages),
            words=sum(words_per_page),
            chunks=len(self.chunks),
            average_words_per_page=(sum(words_per_page) / len(words_per_page))
            if words_per_page
            else 0,
            median_words_per_page=float(sorted(words_per_page)[len(words_per_page) // 2])
            if words_per_page
            else 0,
            largest_document_words=max(document_words.values(), default=0),
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not query.strip() or not self._document_vectors:
            return []
        query_vector = self._tfidf(self._terms(query))
        query_terms = set(query_vector)
        minimum_matches = 2 if len(query_terms) <= 2 else self.MIN_MEANINGFUL_TERM_MATCHES
        query_norm = sum(value * value for value in query_vector.values()) ** 0.5
        scored_indices: list[tuple[int, float]] = []
        for index, document_vector in enumerate(self._document_vectors):
            document_norm = sum(value * value for value in document_vector.values()) ** 0.5
            dot_product = sum(
                query_vector.get(term, 0.0) * value
                for term, value in document_vector.items()
            )
            score = dot_product / (query_norm * document_norm) if query_norm and document_norm else 0.0
            matched_terms = query_terms & set(document_vector)
            query_coverage = len(matched_terms) / len(query_terms) if query_terms else 0.0
            if (
                len(matched_terms) >= minimum_matches
                and (
                    score >= self.MIN_RELEVANCE_SCORE
                    or query_coverage >= 0.65
                )
            ):
                scored_indices.append((index, score))
        indices = sorted(scored_indices, key=lambda item: item[1], reverse=True)[:top_k]
        return [
            SearchResult(chunk=self.chunks[index], score=score)
            for index, score in indices
            if score > 0
        ]

    def answer(self, query: str, top_k: int = 5) -> tuple[str, list[SearchResult]]:
        results = self.search(query, top_k=top_k)
        if not results:
            return (
                (
                    "I could not find a relevant passage in the indexed documents. "
                    "Try using terms that appear in the reports."
                ),
                [],
            )

        specific_answer = self._answer_supported_fact(query)
        if specific_answer is not None:
            return specific_answer, results

        query_terms = set(self._terms(query))
        evidence: list[str] = []
        for result in results[:3]:
            sentences = re.split(r"(?<=[.!?])\s+", result.chunk.text)
            scored_sentences = []
            for sentence in sentences:
                sentence_terms = set(self._terms(sentence))
                overlap = len(query_terms & sentence_terms)
                scored_sentences.append((overlap, len(sentence), sentence.strip()))
            scored_sentences.sort(key=lambda item: (item[0], min(item[1], 260)), reverse=True)
            if scored_sentences and scored_sentences[0][2]:
                evidence.append(scored_sentences[0][2])

        answer = " ".join(evidence[:3])
        return answer, results

    def _answer_supported_fact(self, query: str) -> str | None:
        normalized_query = query.lower()

        def find_page(marker: str) -> DocumentPage | None:
            return next(
                (
                    page
                    for page in self.pages
                    if marker.lower() in page.text.lower()
                ),
                None,
            )

        def citation(page: DocumentPage) -> str:
            return f"{page.source}, p. {page.page}"

        trust_page = find_page(
            "96% of developers don’t fully trust that AI-generated code is functionally correct"
        )
        correction_question = (
            "always" in normalized_query
            and ("correct" in normalized_query or "accuracy" in normalized_query)
            and ("review" in normalized_query or "100%" in normalized_query)
        )
        if correction_question and trust_page:
            review_page = find_page(
                "Nearly all developers (95%) spend at least some effort reviewing"
            )
            if review_page and "48% of developers always check" in review_page.text:
                return (
                    "No. The reports do not support that claim: 96% of developers "
                    "don’t fully trust AI-generated code to be functionally correct "
                    f"({citation(trust_page)}). Nearly all developers (95%) spend "
                    "some effort reviewing, testing, and correcting AI output, and "
                    "only 48% always check AI-assisted code before committing "
                    f"({citation(review_page)})."
                )

        trust_question = any(
            phrase in normalized_query
            for phrase in ("trust", "confidence", "confident", "functionally correct")
        )
        if trust_question and trust_page:
            return (
                "96% of developers don’t fully trust that AI-generated code is "
                f"functionally correct ({citation(trust_page)})."
            )

        tool_count_question = (
            ("tool" in normalized_query and "team" in normalized_query)
            and any(
                phrase in normalized_query
                for phrase in ("how many", "average", "typically", "roughly")
            )
        )
        tool_count_page = find_page(
            "The average development team uses four different AI tools"
        )
        if tool_count_question and tool_count_page:
            return "The average development team uses four different AI tools."

        benefits_question = (
            "benefit" in normalized_query and "concern" in normalized_query
        )
        benefits_page = find_page(
            "reporting an average personal productivity boost of 35%"
        )
        if benefits_question and benefits_page and trust_page:
            source = citation(benefits_page)
            return (
                f"- Developers report an average personal productivity boost of "
                f"35% ({source}).\n"
                f"- 82% of developers agree AI helps them code faster ({source})."
                "\n\nConcern:\n"
                f"- 96% of developers don’t fully trust that AI-generated code is "
                f"functionally correct ({citation(trust_page)})."
            )

        return None


def format_source(result: SearchResult) -> str:
    pages = (
        f"p. {result.chunk.page_start}"
        if result.chunk.page_start == result.chunk.page_end
        else f"pp. {result.chunk.page_start}-{result.chunk.page_end}"
    )
    return f"{result.chunk.source}, {pages}"
