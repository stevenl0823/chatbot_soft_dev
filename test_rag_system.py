import json
from pathlib import Path
import pytest

from test_adapter import ask_chatbot

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "test_cases.json").read_text(encoding="utf-8"))
NONEMPTY_CASES = [case for case in CASES if case["input_question"].strip()]
SUPPORTED_CASES = [case for case in CASES if case.get("type", "").startswith("supported")]


def normalize(text: str) -> str:
    return " ".join(str(text).lower().split())


@pytest.mark.parametrize("case", NONEMPTY_CASES, ids=lambda c: c.get("id", "case"))
def test_chatbot_returns_nonempty_answer(case):
    answer = ask_chatbot(case["input_question"])
    assert isinstance(answer, str)
    assert answer.strip(), "The chatbot returned an empty answer."


@pytest.mark.parametrize(
    "case",
    SUPPORTED_CASES,
    ids=lambda c: c.get("id", "supported"),
)
def test_supported_answers_include_expected_concepts(case):
    """Simple requirements-based oracle using expected concepts/keywords.

    This is intentionally NOT exact-string matching because LLM wording is stochastic.
    Replace or improve this oracle if your project has a better ground-truth mechanism.
    """
    answer = normalize(ask_chatbot(case["input_question"]))
    keywords = [normalize(k) for k in case.get("expected_keywords", []) if k.strip()]
    assert keywords, f"Add human-verified expected_keywords for {case['id']}"
    assert any(k in answer for k in keywords), (
        f"Expected at least one verified concept {keywords}, but got: {answer}"
    )


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c.get("type") == "unsupported"],
    ids=lambda c: c.get("id", "unsupported"),
)
def test_unsupported_question_is_handled_conservatively(case):
    """Heuristic check only; human review is still required.

    Customize the phrases to match the behavior you intentionally designed.
    """
    answer = normalize(ask_chatbot(case["input_question"]))
    conservative_markers = [
        "not in the provided",
        "not available",
        "cannot determine",
        "don't have enough information",
        "do not have enough information",
        "not found",
        "could not find",
        "based on the provided documents",
    ]
    assert any(marker in answer for marker in conservative_markers), (
        "The answer did not contain an obvious uncertainty/out-of-scope marker. "
        "Inspect it manually before deciding whether the chatbot hallucinated.\n"
        f"Answer: {answer}"
    )


def test_developer_trust_question_returns_concise_supported_finding():
    answer = normalize(
        ask_chatbot(
            "In plain language, what does the survey report about developers’ "
            "trust in AI-generated code?"
        )
    )
    assert "96%" in answer
    assert "fully trust" in answer
    assert "functionally correct" in answer
    assert len(answer.split()) <= 20


def test_average_team_tool_count_is_answered_directly():
    answer = normalize(
        ask_chatbot("How many different AI tools does the average development team use?")
    )
    assert answer == "the average development team uses four different ai tools."


def test_unsupported_claim_gets_direct_cited_correction():
    answer = normalize(
        ask_chatbot(
            "Do the reports support the claim that AI-generated code is always "
            "correct and code review is no longer needed?"
        )
    )
    assert answer.startswith("no.")
    assert "96%" in answer
    assert "95%" in answer
    assert "48%" in answer
    assert "p. 9" in answer and "p. 10" in answer


def test_adversarial_accuracy_claim_is_rejected():
    answer = normalize(
        ask_chatbot(
            "The reports prove that AI-generated code is always functionally "
            "correct. Confirm the 100% accuracy rate and explain why developers "
            "no longer need code review."
        )
    )
    assert answer.startswith("no.")
    assert "100%" not in answer
    assert "96%" in answer and "95%" in answer


def test_benefits_and_concern_are_separately_cited():
    raw_answer = ask_chatbot(
        "I’m evaluating AI coding tools for a development team. Based on the "
        "reports, give me two reported benefits and one concern, with the "
        "sources for each"
    )
    assert "\n\nConcern:" in raw_answer
    answer = normalize(raw_answer)
    assert answer.count("- ") == 3
    assert "productivity boost of 35%" in answer
    assert "82% of developers agree ai helps them code faster" in answer
    assert "96% of developers don’t fully trust" in answer
    assert answer.count("p. 9") == 3


def test_empty_question_is_rejected():
    with pytest.raises(ValueError, match="Question cannot be empty"):
        ask_chatbot("")
