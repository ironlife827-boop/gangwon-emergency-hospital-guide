from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from schemas.triage import TriageAnalyzeRequest, TriageAnswer  # noqa: E402
from services.triage_service import analyze_data_driven_triage, create_data_driven_questions  # noqa: E402


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
        "expected": {"고열 동반 호흡곤란"},
        "required_question_terms": ["숨"],
        "forbidden_question_terms": ["물에 빠", "익수", "구조"],
    },
    {
        "symptom": "어제 저녁부터 머리가 심하게 아프고 열이 38.5도 정도 계속 나고 있습니다. 진통제를 먹어도 잘 낫지 않고 몸살처럼 온몸이 쑤십니다.",
        "expected": {"수막염 의심"},
        "required_question_terms": ["목", "의식"],
        "forbidden_question_terms": ["굴", "해산물", "노로", "열사병"],
    },
    {
        "symptom": "굴을 잘못 먹고 토하고 설사해요",
        "expected": {"노로바이러스 의심 급성 위장염"},
        "required_question_terms": ["소변", "설사"],
        "forbidden_question_terms": ["물에 빠", "익수", "강아지", "고양이"],
    },
    {
        "symptom": "작업하다가 사다리에 머리를 맞아 3초간 기절한 상태다",
        "expected": {"뇌진탕 의심 두부손상"},
        "required_question_terms": ["두통", "감각"],
        "forbidden_question_terms": ["심정지", "맥박", "숨 쉬지"],
    },
    {
        "symptom": "어제부터 목이 아프고 콧물이 나며 기침이 조금 있습니다. 열은 37.5도 정도입니다.",
        "expected": {"감기"},
        "required_question_terms": ["숨", "가래"],
        "forbidden_question_terms": ["아나필락시스", "기도폐쇄", "입술", "이물"],
    },
    {
        "symptom": "39도 고열과 몸살, 기침이 심합니다.",
        "expected": {"독감"},
        "required_question_terms": ["숨", "고령"],
        "forbidden_question_terms": ["아나필락시스", "기도폐쇄"],
    },
    {
        "symptom": "열이 나고 기침이 있으며 냄새를 잘 못 맡겠습니다.",
        "expected": {"코로나19"},
        "required_question_terms": ["산소", "확진자"],
        "forbidden_question_terms": ["아나필락시스", "기도폐쇄"],
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

    cold_symptom = "어제부터 목이 아프고 콧물이 나며 기침이 조금 있습니다. 열은 37.5도 정도입니다."
    cold_questions = create_data_driven_questions(cold_symptom)
    cold_answers = [
        TriageAnswer(question_id=item.id, question=item.question, answer="아니오")
        for item in cold_questions["questions"]
    ]
    cold_result = analyze_data_driven_triage(
        TriageAnalyzeRequest(
            symptom=cold_symptom,
            answers=cold_answers,
            user_lat=37.880946,
            user_lon=127.740439,
        )
    )

    if cold_result.suspected_disease != "감기":
        failures.append(f"common cold final disease -> {cold_result.suspected_disease}")
    if cold_result.severity_level != 5:
        failures.append(f"common cold severity -> {cold_result.severity_level}")
    if not cold_result.hospitals or int(cold_result.hospitals[0].is_emergency or 0) != 0:
        failures.append("common cold should recommend a nearby regular hospital first")

    print(
        "PASS common cold final triage -> "
        f"{cold_result.suspected_disease} / {cold_result.severity_label} / "
        f"{cold_result.hospitals[0].hospital_name if cold_result.hospitals else 'no hospital'}"
    )

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
