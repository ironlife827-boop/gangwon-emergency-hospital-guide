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
        "expected": {"소아 고열 경련", "열성경련", "열사병"},
        "required_question_terms": ["경련", "의식"],
    },
    {
        "symptom": "토하고 설사하고 탈수 같아요",
        "expected": {"탈수", "중증 탈수"},
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


COMMON_DISEASE_CASES = [
    ("감기", "목이 아프고 콧물이 나며 기침이 있습니다.", {"감기"}),
    ("독감", "39도 고열과 몸살, 기침이 심합니다.", {"독감"}),
    ("코로나19", "열이 나고 기침이 있으며 냄새를 잘 못 맡겠습니다.", {"코로나19"}),
    ("편도염", "목이 너무 아프고 침 삼키기 힘듭니다.", {"편도염"}),
    ("기관지염", "기침이 2주째 계속되고 가래가 나옵니다.", {"기관지염"}),
    ("폐렴", "고열이 있고 기침할 때 가슴이 아픕니다.", {"폐렴"}),
    ("천식", "숨이 차고 쌕쌕거리는 소리가 납니다.", {"천식"}),
    ("알레르기 비염", "재채기와 콧물이 계속 납니다.", {"알레르기 비염"}),
    ("중이염", "귀가 아프고 잘 들리지 않습니다.", {"중이염"}),
    ("결막염", "눈이 충혈되고 눈곱이 많이 낍니다.", {"결막염"}),
    ("편두통", "한쪽 머리가 욱신거리고 빛을 보면 심해집니다.", {"편두통"}),
    ("긴장성 두통", "머리가 띠를 두른 것처럼 조여옵니다.", {"긴장성 두통"}),
    ("뇌수막염", "고열과 심한 두통, 목이 뻣뻣합니다.", {"뇌수막염", "수막염 의심"}),
    ("뇌졸중", "갑자기 한쪽 팔에 힘이 빠지고 말이 어눌해졌습니다.", {"뇌졸중"}),
    ("치매 초기", "최근 기억이 자꾸 나지 않습니다.", {"치매 초기"}),
    ("공황장애", "갑자기 심장이 뛰고 숨쉬기 힘들어졌습니다.", {"공황장애"}),
    ("우울증", "아무것도 하기 싫고 계속 우울합니다.", {"우울증"}),
    ("불면증", "잠들기 어렵고 자주 깹니다.", {"불면증"}),
    ("역류성 식도염", "속이 쓰리고 신물이 올라옵니다.", {"역류성 식도염"}),
    ("위염", "명치가 쓰리고 속이 불편합니다.", {"위염"}),
    ("위궤양", "식사 후 명치 통증이 심합니다.", {"위궤양"}),
    ("장염", "설사와 복통이 계속됩니다.", {"장염"}),
    ("과민성대장증후군", "긴장하면 배가 아프고 설사를 합니다.", {"과민성대장증후군"}),
    ("맹장염", "오른쪽 아랫배가 심하게 아픕니다.", {"맹장염", "급성 충수염"}),
    ("담석증", "오른쪽 윗배가 아프고 구역질이 납니다.", {"담석증"}),
    ("간염", "피부와 눈이 노랗게 변했습니다.", {"간염"}),
    ("신장결석", "옆구리가 찢어질 듯 아픕니다.", {"신장결석"}),
    ("방광염", "소변 볼 때 따갑고 자주 마렵습니다.", {"방광염"}),
    ("요로감염", "열이 나고 소변 볼 때 통증이 있습니다.", {"요로감염"}),
    ("전립선염", "회음부 통증과 배뇨 불편이 있습니다.", {"전립선염"}),
    ("당뇨병", "물을 자주 마시고 소변을 많이 봅니다.", {"당뇨병"}),
    ("저혈당", "식은땀이 나고 손이 떨립니다.", {"저혈당"}),
    ("갑상선 기능 항진증", "심장이 빨리 뛰고 체중이 줄고 있습니다.", {"갑상선 기능 항진증"}),
    ("갑상선 기능 저하증", "피곤하고 체중이 늘고 있습니다.", {"갑상선 기능 저하증"}),
    ("고혈압", "뒷목이 당기고 머리가 아픕니다.", {"고혈압"}),
    ("협심증", "운동하면 가슴이 조이는 느낌이 납니다.", {"협심증"}),
    ("심근경색", "가슴을 짓누르는 통증과 식은땀이 납니다.", {"심근경색", "급성 심근경색"}),
    ("부정맥", "심장이 불규칙하게 뜁니다.", {"부정맥"}),
    ("심부전", "조금만 걸어도 숨이 찹니다.", {"심부전"}),
    ("아토피", "피부가 가렵고 붉게 변했습니다.", {"아토피"}),
    ("두드러기", "피부에 붉은 발진이 갑자기 생겼습니다.", {"두드러기"}),
    ("대상포진", "몸 한쪽에 물집과 통증이 있습니다.", {"대상포진"}),
    ("무좀", "발가락 사이가 가렵고 벗겨집니다.", {"무좀"}),
    ("류마티스 관절염", "아침에 손가락 관절이 뻣뻣합니다.", {"류마티스 관절염"}),
    ("통풍", "엄지발가락이 붓고 극심하게 아픕니다.", {"통풍"}),
    ("디스크", "허리가 아프고 다리까지 저립니다.", {"디스크"}),
    ("오십견", "어깨가 아프고 팔이 잘 안 올라갑니다.", {"오십견"}),
    ("골절", "넘어졌는데 팔이 붓고 움직일 수 없습니다.", {"골절"}),
    ("빈혈", "어지럽고 쉽게 피곤합니다.", {"빈혈"}),
    ("패혈증", "고열과 의식 저하가 있습니다.", {"패혈증 의심"}),
    ("아나필락시스", "음식 먹은 뒤 입술이 붓고 숨쉬기 힘듭니다.", {"아나필락시스"}),
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
        if not response.get("disease_id"):
            failures.append(f"{case['symptom']} missing disease_id")
        if not response.get("disease_candidates"):
            failures.append(f"{case['symptom']} missing disease candidates")

        for term in case.get("required_question_terms", []):
            if term not in questions:
                failures.append(f"{case['symptom']} missing question term: {term}")

        for term in case.get("forbidden_question_terms", []):
            if term in questions:
                failures.append(f"{case['symptom']} contains forbidden question term: {term}")

        print(f"PASS {case['symptom']} -> {disease} / {len(response['questions'])} questions")

    for label, symptom, expected in COMMON_DISEASE_CASES:
        response = create_data_driven_questions(symptom)
        disease = response["suspected_disease"]
        if disease not in expected:
            failures.append(f"{label}: {symptom} -> {disease}, expected one of {sorted(expected)}")
        if not response.get("disease_id"):
            failures.append(f"{label}: {symptom} missing disease_id")

        print(f"PASS common table {label} -> {disease}")

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
    if not cold_result.disease_id:
        failures.append("common cold final triage missing disease_id")
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
