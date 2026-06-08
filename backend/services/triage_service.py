from __future__ import annotations

import pandas as pd

from schemas.triage import AnalysisEvidence, TriageAnalyzeRequest, TriageAnalyzeResponse, TriageQuestion
from services.data_loader import load_disease_questions, load_severity_model, load_triage_rules
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

def _normalize_text(text: str) -> str:
    return str(text).lower().replace(" ", "").replace(",", "").replace(".", "")

def _contains_any_keyword(symptom: str, keyword_text: str) -> bool:
    symptom_norm = _normalize_text(symptom)
    keywords = [_normalize_text(k) for k in str(keyword_text).split(";") if str(k).strip()]
    return any(k and k in symptom_norm for k in keywords)

def _severity_label(level: int) -> str:
    labels = {1: "매우 긴급", 2: "긴급", 3: "주의", 4: "낮음", 5: "비응급"}
    return labels.get(level, "주의")

def _rewrite_question(raw_question: str) -> str:
    raw_question = str(raw_question).strip()
    for keyword, rewritten in QUESTION_REWRITE_MAP.items():
        if keyword in raw_question:
            return rewritten
    question = raw_question.replace(" 증상 증상이 있습니까?", " 증상이 있나요?")
    question = question.replace(" 증상이 있습니까?", " 증상이 있나요?")
    question = question.replace("있습니까?", "있나요?")
    return question

def _rule_row_to_question(row) -> TriageQuestion:
    return TriageQuestion(id=str(row["question_id"]), question=_rewrite_question(str(row["question"])), options=["예", "아니오", "잘 모르겠음"], allow_custom=False)

def _select_fallback_triage_questions(symptom_group: str, existing_question_ids: set[str], limit: int) -> list[TriageQuestion]:
    rules = load_triage_rules()
    group_rules = rules[rules["symptom_group"] == symptom_group].copy()
    if group_rules.empty:
        group_rules = rules.copy()
    group_rules = group_rules.sort_values("risk_score", ascending=False)
    questions: list[TriageQuestion] = []
    for _, row in group_rules.iterrows():
        question_id = str(row["question_id"])
        if question_id in existing_question_ids:
            continue
        questions.append(_rule_row_to_question(row))
        existing_question_ids.add(question_id)
        if len(questions) >= limit:
            break
    return questions

def _select_dynamic_questions(symptom: str, analysis: dict, limit: int = 4) -> list[TriageQuestion]:
    disease_questions = load_disease_questions()
    selected: list[TriageQuestion] = []
    selected_ids: set[str] = set()
    if not disease_questions.empty:
        disease = str(analysis.get("suspected_disease", ""))
        symptom_group = str(analysis.get("symptom_group", ""))
        exact_rows = disease_questions[disease_questions["suspected_disease"].eq(disease)].copy()
        group_rows = disease_questions[disease_questions["symptom_group"].eq(symptom_group) & ~disease_questions["suspected_disease"].eq(disease)].copy()
        candidate_rows = pd.concat([exact_rows, group_rows], ignore_index=True)
        candidate_rows = candidate_rows.sort_values(["importance", "risk_score"], ascending=[False, False])
        for _, row in candidate_rows.iterrows():
            question_id = str(row["question_id"])
            if question_id in selected_ids:
                continue
            if _contains_any_keyword(symptom, str(row.get("positive_keywords", ""))):
                continue
            selected.append(TriageQuestion(id=question_id, question=str(row["question"]), options=["예", "아니오", "잘 모르겠음"], allow_custom=False))
            selected_ids.add(question_id)
            if len(selected) >= limit:
                break
    min_questions = 1 if analysis.get("matched_by") == "keyword_rule" else 2
    if len(selected) < min_questions:
        selected.extend(_select_fallback_triage_questions(str(analysis.get("symptom_group", "")), selected_ids, min_questions - len(selected)))
    return selected[:limit]

def _build_evidence(analysis: dict) -> AnalysisEvidence:
    matched_by = analysis.get("matched_by", "similarity")
    top_score = float(analysis.get("max_similarity", 0))
    if matched_by == "keyword_rule":
        explanation = "고위험 응급 키워드가 탐지되어 응급 키워드 룰을 우선 적용했습니다."
    elif matched_by == "trained_classifier":
        explanation = "자체 수집한 네이버 지식인 증상 사례 데이터로 학습한 symptom_classifier.pkl 모델이 증상군·진료과·의심질환을 예측했습니다."
    else:
        explanation = "네이버 지식인 실제 증상 사례와의 TF-IDF 유사도 검색 결과를 기반으로 추론했습니다."
    return AnalysisEvidence(method=matched_by, model_used=matched_by == "trained_classifier", keyword_rule_used=matched_by == "keyword_rule", similarity_top_score=round(top_score, 4), explanation=explanation)

def create_data_driven_questions(symptom: str) -> dict:
    analysis = analyze_symptom_text(symptom)
    questions = _select_dynamic_questions(symptom=symptom, analysis=analysis, limit=4)
    return {"symptom": symptom, "symptom_group": analysis["symptom_group"], "department": analysis["department"], "suspected_disease": analysis["suspected_disease"], "need_followup": len(questions) > 0, "questions": questions, "similar_cases": analysis["similar_cases"], "evidence": _build_evidence(analysis)}

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

def _build_question_score_map() -> dict:
    rules = load_triage_rules()
    disease_questions = load_disease_questions()
    score_map: dict[str, dict] = {}
    for _, row in rules.iterrows():
        score_map[str(row["question_id"])] = {"risk_score": float(row.get("risk_score", 0)), "required_resource_code": str(row.get("required_resource_code", ""))}
    for _, row in disease_questions.iterrows():
        score_map[str(row["question_id"])] = {"risk_score": float(row.get("risk_score", 0)), "required_resource_code": str(row.get("required_resource_code", ""))}
    return score_map

def _primary_case_disease(symptom_analysis: dict) -> str:
    similar_cases = symptom_analysis.get("similar_cases", [])
    if similar_cases:
        first_case = similar_cases[0]
        if first_case.suspected_disease:
            return first_case.suspected_disease
    return symptom_analysis["suspected_disease"]

def _build_final_symptom_summary(payload: TriageAnalyzeRequest) -> str:
    """
    사용자 최초 입력과 추가 문진 답변을 합쳐 최종 분석용 증상 문장으로 정리한다.
    이 문장은 최종 결과 화면에 표시되고, 분석 모델 입력에도 활용된다.
    """
    lines = [f"초기 증상: {payload.symptom.strip()}"]

    if payload.answers:
        lines.append("추가 문진 답변:")
        for answer in payload.answers:
            value = str(answer.answer).strip()
            if answer.custom_answer:
                value = f"{value} ({answer.custom_answer.strip()})"
            lines.append(f"- {answer.question}: {value}")

    return "\n".join(lines)


def _build_analysis_text(payload: TriageAnalyzeRequest) -> str:
    """
    분류 모델에는 '예/잘 모르겠음' 답변을 중심으로 보강한다.
    '아니오' 답변의 질문 문구를 그대로 넣으면 오히려 해당 증상 키워드가 포함되어
    분류 모델을 혼동시킬 수 있으므로 모델 입력에서는 제외한다.
    """
    parts = [payload.symptom.strip()]

    for answer in payload.answers:
        normalized_answer = str(answer.answer).strip().lower()

        if answer.answer in YES_VALUES or normalized_answer in YES_VALUES:
            parts.append(str(answer.question))
            if answer.custom_answer:
                parts.append(str(answer.custom_answer))

        elif answer.answer in UNKNOWN_VALUES or normalized_answer in UNKNOWN_VALUES:
            parts.append(f"불확실: {answer.question}")

    return " ".join(part for part in parts if part)


def analyze_data_driven_triage(payload: TriageAnalyzeRequest) -> TriageAnalyzeResponse:
    final_symptom_summary = _build_final_symptom_summary(payload)
    analysis_text = _build_analysis_text(payload)

    # 최종 분석은 최초 입력만이 아니라 문진 답변까지 반영한 문장을 기준으로 수행한다.
    symptom_analysis = analyze_symptom_text(analysis_text)

    question_score_map = _build_question_score_map()
    total_risk_score = 0.0
    matched_resource_codes: list[str] = []

    for answer in payload.answers:
        rule = question_score_map.get(answer.question_id)
        if not rule:
            continue

        added_score = _answer_to_score(answer.answer, float(rule.get("risk_score", 0)))
        total_risk_score += added_score

        if added_score > 0:
            matched_resource_codes.append(str(rule.get("required_resource_code", "")))

    naver_level = int(symptom_analysis["naver_severity_level"])
    combined_risk_score = max(total_risk_score, max(0, naver_level - 1))
    severity_level = _predict_severity_from_score(combined_risk_score)

    required_resource_code = (
        matched_resource_codes[0]
        if matched_resource_codes
        else _resource_code_from_group(symptom_analysis["symptom_group"])
    )

    hospitals = recommend_hospitals(
        department=symptom_analysis["department"],
        severity_level=severity_level,
        user_lat=payload.user_lat,
        user_lon=payload.user_lon,
        limit=3,
    )

    evidence = _build_evidence(symptom_analysis)

    summary = (
        "사용자 최초 입력과 추가 문진 답변을 합쳐 최종 증상 문장을 구성한 뒤, "
        f"이를 기준으로 '{symptom_analysis['symptom_group']}' 증상군, "
        f"{symptom_analysis['department']} 진료과, "
        f"{_primary_case_disease(symptom_analysis)} 가능성을 산출했습니다. "
        f"동적 문진 위험 점수와 응급도 모델을 결합해 응급도 {severity_level}단계로 판단했습니다."
    )

    return TriageAnalyzeResponse(
        final_symptom_summary=final_symptom_summary,
        severity_level=severity_level,
        severity_label=_severity_label(severity_level),
        risk_score=int(round(combined_risk_score)),
        required_resource_code=required_resource_code,
        symptom_group=symptom_analysis["symptom_group"],
        department=symptom_analysis["department"],
        suspected_disease=_primary_case_disease(symptom_analysis),
        summary=summary,
        evidence=evidence,
        similar_cases=symptom_analysis["similar_cases"],
        hospitals=hospitals,
    )


def _resource_code_from_group(symptom_group: str) -> str:
    mapping = {"cardio": "ER_CARDIO", "neuro": "ER_NEURO", "respiratory": "ER_RESP", "abdominal": "ER_GENERAL", "trauma": "ER_TRAUMA", "orthopedic": "ER_TRAUMA", "bleeding": "ER_TRAUMA", "pediatric": "ER_PED", "allergy": "ER_GENERAL", "infection": "ER_GENERAL", "toxic": "ER_GENERAL", "poisoning": "ER_GENERAL"}
    return mapping.get(symptom_group, "ER_GENERAL")
