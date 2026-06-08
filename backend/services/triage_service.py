from __future__ import annotations

import pandas as pd

from schemas.triage import (
    TriageAnalyzeRequest,
    TriageAnalyzeResponse,
    TriageQuestion,
)
from services.data_loader import load_severity_model, load_triage_rules
from services.recommendation_service import recommend_hospitals
from services.symptom_analyzer import analyze_symptom_text


YES_VALUES = {"예", "네", "있음", "그렇다", "맞음", "yes", "y"}
UNKNOWN_VALUES = {"잘 모르겠음", "모름", "unknown"}


QUESTION_REWRITE_MAP = {
    "심폐소생술이 필요한 증상": "의식이 없거나 호흡이 멈춘 것처럼 보이나요?",
    "급성호흡곤란": "갑자기 숨쉬기 어렵거나 숨이 차나요?",
    "쇼크": "식은땀, 창백함, 심한 어지러움 또는 쓰러질 것 같은 증상이 있나요?",
    "심장질환으로 인한 급성 흉통": "가슴 통증이나 가슴이 조이는 느낌이 있나요?",
    "중증외상": "교통사고, 추락, 심한 충격 등 큰 외상이 있었나요?",
    "심한 출혈": "피가 멈추지 않거나 출혈량이 많나요?",
    "뇌졸중": "한쪽 팔·다리 힘 빠짐, 말 어눌함, 얼굴 비대칭이 있나요?",
    "의식장애": "의식이 흐려지거나 부르면 반응이 둔한가요?",
    "경련": "몸이 떨리거나 경련 증상이 있었나요?",
    "급성 복통": "갑자기 심한 복통이 있나요?",
    "고열": "고열이 있거나 열이 계속 오르나요?",
    "탈수": "심한 구토·설사, 소변 감소, 입마름이 있나요?",
    "알레르기": "두드러기, 얼굴·입술 부종, 숨참이 동반되나요?",
}


def _severity_label(level: int) -> str:
    labels = {
        1: "매우 긴급",
        2: "긴급",
        3: "주의",
        4: "낮음",
        5: "비응급",
    }
    return labels.get(level, "주의")


def _rewrite_question(raw_question: str) -> str:
    raw_question = str(raw_question).strip()

    for keyword, rewritten in QUESTION_REWRITE_MAP.items():
        if keyword in raw_question:
            return rewritten

    # 기본 정제: "증상 증상" 같은 중복 표현 제거
    question = raw_question.replace(" 증상 증상이 있습니까?", " 증상이 있나요?")
    question = question.replace(" 증상이 있습니까?", " 증상이 있나요?")
    question = question.replace("있습니까?", "있나요?")
    return question


def _select_triage_questions(symptom_group: str, limit: int = 4) -> list[TriageQuestion]:
    rules = load_triage_rules()

    group_rules = rules[rules["symptom_group"] == symptom_group].copy()
    if group_rules.empty:
        group_rules = rules.copy()

    group_rules = group_rules.sort_values("risk_score", ascending=False)

    questions: list[TriageQuestion] = []
    used_question_ids: set[str] = set()

    for _, row in group_rules.iterrows():
        question_id = str(row["question_id"])
        if question_id in used_question_ids:
            continue

        questions.append(
            TriageQuestion(
                id=question_id,
                question=_rewrite_question(str(row["question"])),
                options=["예", "아니오", "잘 모르겠음"],
                allow_custom=False,
            )
        )
        used_question_ids.add(question_id)

        if len(questions) >= limit:
            break

    return questions


def create_data_driven_questions(symptom: str) -> dict:
    analysis = analyze_symptom_text(symptom)
    questions = _select_triage_questions(analysis["symptom_group"])

    return {
        "symptom": symptom,
        "symptom_group": analysis["symptom_group"],
        "department": analysis["department"],
        "suspected_disease": analysis["suspected_disease"],
        "need_followup": len(questions) > 0,
        "questions": questions[:4],
        "similar_cases": analysis["similar_cases"],
    }


def _answer_to_score(answer: str, rule_score: float) -> float:
    normalized = str(answer).strip().lower()

    if answer in YES_VALUES or normalized in YES_VALUES:
        return float(rule_score)

    if answer in UNKNOWN_VALUES or normalized in UNKNOWN_VALUES:
        return float(rule_score) * 0.4

    return 0.0


def _predict_severity_from_score(risk_score: float) -> int:
    model = load_severity_model()

    if model is not None:
        try:
            prediction = int(model.predict(pd.DataFrame([{"risk_score": risk_score}]))[0])
            return max(1, min(5, prediction))
        except Exception:
            pass

    if risk_score >= 5:
        return 1
    if risk_score >= 4:
        return 2
    if risk_score >= 3:
        return 3
    if risk_score >= 1:
        return 4
    return 5


def _primary_case_disease(symptom_analysis: dict) -> str:
    similar_cases = symptom_analysis.get("similar_cases", [])
    if similar_cases:
        first_case = similar_cases[0]
        if first_case.suspected_disease:
            return first_case.suspected_disease
    return symptom_analysis["suspected_disease"]


def analyze_data_driven_triage(payload: TriageAnalyzeRequest) -> TriageAnalyzeResponse:
    symptom_analysis = analyze_symptom_text(payload.symptom)
    rules = load_triage_rules()

    rule_map = rules.set_index("question_id").to_dict(orient="index")

    total_risk_score = 0.0
    matched_resource_codes: list[str] = []

    for answer in payload.answers:
        rule = rule_map.get(answer.question_id)
        if not rule:
            continue

        rule_score = float(rule.get("risk_score", 0))
        added_score = _answer_to_score(answer.answer, rule_score)
        total_risk_score += added_score

        if added_score > 0:
            matched_resource_codes.append(str(rule.get("required_resource_code", "")))

    # 네이버 사례 severity_level은 숫자가 클수록 위험하므로 위험 점수 참고값으로 변환한다.
    naver_level = int(symptom_analysis["naver_severity_level"])
    naver_based_risk = max(0, naver_level - 1)

    combined_risk_score = max(total_risk_score, naver_based_risk)
    severity_level = _predict_severity_from_score(combined_risk_score)

    required_resource_code = (
        matched_resource_codes[0]
        if matched_resource_codes
        else _resource_code_from_group(symptom_analysis["symptom_group"])
    )

    # 의심질환은 문진 질문의 극단적 질환명보다 유사 사례 기반 결과를 우선한다.
    suspected_disease = _primary_case_disease(symptom_analysis)

    hospitals = recommend_hospitals(
        department=symptom_analysis["department"],
        severity_level=severity_level,
        user_lat=payload.user_lat,
        user_lon=payload.user_lon,
        limit=3,
    )

    summary = (
        f"입력 증상은 '{symptom_analysis['symptom_group']}' 증상군과 가장 유사하며, "
        f"추천 진료과는 {symptom_analysis['department']}입니다. "
        f"네이버 실제 사례 유사도, 문진 위험 점수, 응급도 모델을 결합해 "
        f"응급도 {severity_level}단계로 산출했습니다."
    )

    return TriageAnalyzeResponse(
        severity_level=severity_level,
        severity_label=_severity_label(severity_level),
        risk_score=int(round(combined_risk_score)),
        required_resource_code=required_resource_code,
        symptom_group=symptom_analysis["symptom_group"],
        department=symptom_analysis["department"],
        suspected_disease=suspected_disease,
        summary=summary,
        similar_cases=symptom_analysis["similar_cases"],
        hospitals=hospitals,
    )


def _resource_code_from_group(symptom_group: str) -> str:
    mapping = {
        "cardio": "ER_CARDIO",
        "neuro": "ER_NEURO",
        "respiratory": "ER_RESP",
        "abdominal": "ER_GENERAL",
        "trauma": "ER_TRAUMA",
        "orthopedic": "ER_TRAUMA",
        "bleeding": "ER_TRAUMA",
        "pediatric": "ER_PED",
        "allergy": "ER_GENERAL",
        "infection": "ER_GENERAL",
    }
    return mapping.get(symptom_group, "ER_GENERAL")
