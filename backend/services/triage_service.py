from __future__ import annotations

import pandas as pd

from schemas.triage import (
    RecommendedHospital,
    TriageAnalyzeRequest,
    TriageAnalyzeResponse,
    TriageQuestion,
)
from services.data_loader import load_severity_model, load_triage_rules
from services.recommendation_service import recommend_hospitals
from services.symptom_analyzer import analyze_symptom_text


YES_VALUES = {"예", "네", "있음", "그렇다", "맞음", "yes", "y"}
UNKNOWN_VALUES = {"잘 모르겠음", "모름", "unknown"}


def _severity_label(level: int) -> str:
    labels = {
        1: "매우 긴급",
        2: "긴급",
        3: "주의",
        4: "낮음",
        5: "비응급",
    }
    return labels.get(level, "주의")


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
                question=str(row["question"]),
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

    # 입력 문장이 충분히 구체적이고 유사 사례 신뢰도가 높은 경우에도
    # 발표/시연 안정성을 위해 최소 2개 문진은 제공한다.
    need_followup = len(questions) > 0

    return {
        "symptom": symptom,
        "symptom_group": analysis["symptom_group"],
        "department": analysis["department"],
        "suspected_disease": analysis["suspected_disease"],
        "need_followup": need_followup,
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

    # 모델 실패 시 rule fallback. 숫자가 작을수록 긴급.
    if risk_score >= 5:
        return 1
    if risk_score >= 4:
        return 2
    if risk_score >= 3:
        return 3
    if risk_score >= 1:
        return 4
    return 5


def analyze_data_driven_triage(payload: TriageAnalyzeRequest) -> TriageAnalyzeResponse:
    symptom_analysis = analyze_symptom_text(payload.symptom)
    rules = load_triage_rules()

    rule_map = rules.set_index("question_id").to_dict(orient="index")

    total_risk_score = 0.0
    matched_resource_codes: list[str] = []
    matched_diseases: list[str] = []

    for answer in payload.answers:
        rule = rule_map.get(answer.question_id)
        if not rule:
            continue

        rule_score = float(rule.get("risk_score", 0))
        added_score = _answer_to_score(answer.answer, rule_score)
        total_risk_score += added_score

        if added_score > 0:
            matched_resource_codes.append(str(rule.get("required_resource_code", "")))
            matched_diseases.append(str(rule.get("suspected_disease", "")))

    # 질문 답변이 모두 낮게 나와도 유사 사례의 위험도를 최소 참고값으로 사용한다.
    naver_level = int(symptom_analysis["naver_severity_level"])
    naver_based_risk = max(0, naver_level - 1)
    combined_risk_score = max(total_risk_score, naver_based_risk)

    severity_level = _predict_severity_from_score(combined_risk_score)

    required_resource_code = (
        matched_resource_codes[0]
        if matched_resource_codes
        else _resource_code_from_group(symptom_analysis["symptom_group"])
    )

    suspected_disease = (
        matched_diseases[0]
        if matched_diseases
        else symptom_analysis["suspected_disease"]
    )

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
        f"문진 답변과 실제 사례 유사도를 반영해 응급도 {severity_level}단계로 산출했습니다."
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
