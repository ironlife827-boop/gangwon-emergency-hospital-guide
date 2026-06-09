from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from services.triage_service import create_data_driven_questions  # noqa: E402


CASES = [
    {
        "symptom": "오른쪽 팔 감전",
        "expected": {"전기손상"},
        "forbidden_question_terms": ["골절", "척추", "탈구"],
    },
    {
        "symptom": "갑자기 왼팔에 힘이 안 들어가고 말이 어눌해요",
        "expected": {"뇌졸중"},
        "required_question_terms": ["얼굴", "두통"],
    },
    {
        "symptom": "벌에 쏘인 뒤 입술이 붓고 숨쉬기 힘들어요",
        "expected": {"아나필락시스", "벌쏘임"},
        "required_question_terms": ["어지럽", "두드러기"],
    },
    {
        "symptom": "배가 찢어질 듯 아프고 식은땀이 나요",
        "expected": {"복막염", "장폐색", "위장관출혈"},
        "required_question_terms": ["배", "열"],
    },
    {
        "symptom": "가슴이 답답하고 숨이 차요",
        "expected": {"급성 심근경색", "부정맥"},
        "required_question_terms": ["가슴", "왼팔"],
    },
    {
        "symptom": "머리가 깨질듯 아프고 토할 것 같아요",
        "expected": {"뇌졸중"},
        "forbidden_question_terms": ["심장", "맥박"],
    },
    {
        "symptom": "아이 열이 39도이고 경련했어요",
        "expected": {"소아 고열 경련", "열사병"},
        "required_question_terms": ["경련", "의식"],
    },
    {
        "symptom": "토하고 설사하고 탈수 같아요",
        "expected": {"탈수"},
        "required_question_terms": ["소변", "설사"],
        "forbidden_question_terms": ["심정지", "맥박"],
    },
    {
        "symptom": "갑자기 열이 40도까지 나고 숨쉬는게 힘들어요",
        "expected": {"호흡부전"},
        "required_question_terms": ["고열", "숨"],
        "forbidden_question_terms": ["물에 빠", "익수", "구조"],
    },
]


def _question_text(response: dict) -> str:
    return " ".join(question.question for question in response["questions"])


def main() -> None:
    failures: list[str] = []

    for case in CASES:
        response = create_data_driven_questions(case["symptom"])
        disease = response["suspected_disease"]
        questions = _question_text(response)

        if disease not in case["expected"]:
            failures.append(
                f"{case['symptom']} -> {disease}, expected one of {sorted(case['expected'])}"
            )

        for term in case.get("required_question_terms", []):
            if term not in questions:
                failures.append(f"{case['symptom']} missing question term: {term}")

        for term in case.get("forbidden_question_terms", []):
            if term in questions:
                failures.append(f"{case['symptom']} contains forbidden question term: {term}")

        print(f"PASS {case['symptom']} -> {disease} / {len(response['questions'])} questions")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
