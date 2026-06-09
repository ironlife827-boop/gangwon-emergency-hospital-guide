from __future__ import annotations

import pandas as pd

from schemas.triage import (
    AnalysisEvidence,
    TriageAnalyzeRequest,
    TriageAnalyzeResponse,
    TriageQuestion,
)
from services.data_loader import (
    load_disease_questions,
    load_triage_rules,
)
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


def _keyword_in_text(keyword: str, text: str) -> bool:
    keyword_norm = _normalize_text(keyword)
    text_norm = _normalize_text(text)

    if keyword_norm and keyword_norm in text_norm:
        return True

    if keyword_norm.endswith("부음"):
        body = keyword_norm[:-2]
        return any(
            variant in text_norm
            for variant in [f"{body}붓", f"{body}이붓", f"{body}가붓"]
        )

    if keyword_norm.endswith("힘듦"):
        return keyword_norm[:-1] in text_norm

    return False


def _keyword_overlap_count(text: str, keyword_text: str) -> int:
    keywords = [
        str(keyword).strip()
        for keyword in str(keyword_text).split(";")
        if str(keyword).strip()
    ]
    return sum(1 for keyword in keywords if _keyword_in_text(keyword, text))


def _contains_any_keyword(text: str, keyword_text: str) -> bool:
    return _keyword_overlap_count(text, keyword_text) > 0


def _already_covered_by_user_input(text: str, keyword_text: str) -> bool:
    text_norm = _normalize_text(text)
    matched_keywords = []

    for keyword in str(keyword_text).split(";"):
        keyword_norm = _normalize_text(keyword)
        if keyword_norm and _keyword_in_text(keyword_norm, text_norm):
            matched_keywords.append(keyword_norm)

    if len(matched_keywords) >= 2:
        return True

    # 질환명이나 상황 단어 하나만 들어갔다고 질문을 제거하지 않는다.
    return any(len(keyword) >= 3 for keyword in matched_keywords)


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

    question = raw_question.replace(" 증상 증상이 있습니까?", " 증상이 있나요?")
    question = question.replace(" 증상이 있습니까?", " 증상이 있나요?")
    question = question.replace("있습니까?", "있나요?")
    return question


def _rule_row_to_question(row) -> TriageQuestion:
    return TriageQuestion(
        id=str(row["question_id"]),
        question=_rewrite_question(str(row["question"])),
        options=["예", "아니오", "잘 모르겠음"],
        allow_custom=False,
    )


def _select_fallback_triage_questions(
    symptom_group: str,
    existing_question_ids: set[str],
    limit: int,
) -> list[TriageQuestion]:
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


def _score_question(row, symptom: str, analysis: dict) -> float:
    disease = str(analysis.get("suspected_disease", ""))
    disease_id = str(analysis.get("disease_id", ""))
    group = str(analysis.get("symptom_group", ""))

    question_disease = str(row.get("suspected_disease", ""))
    question_disease_id = str(row.get("disease_id", ""))
    question_group = str(row.get("symptom_group", ""))

    risk_score = float(row.get("risk_score", 0))
    importance = float(row.get("importance", 0))
    keywords = str(row.get("positive_keywords", ""))

    disease_id_match = 1 if disease_id and question_disease_id == disease_id else 0
    disease_match = 1 if question_disease == disease else 0
    group_match = 1 if question_group == group else 0
    already_covered = _already_covered_by_user_input(symptom, keywords)

    # 이미 사용자가 말한 핵심 정보를 반복 질문하지 않기 위한 강한 패널티
    already_mentioned_penalty = 12 if already_covered else 0

    score = (
        disease_id_match * 45
        + disease_match * 40
        + group_match * 5
        + risk_score * 2.5
        + importance * 2
        - already_mentioned_penalty
    )

    return score


def _dynamic_question_limit(symptom: str, analysis: dict, ranked_rows: pd.DataFrame) -> int:
    """
    정보가 구체적이면 질문 수를 줄이고,
    짧고 모호하면 질문 수를 늘린다.
    """
    text_len = len(str(symptom).replace(" ", ""))
    confidence = analysis.get("disease_confidence")

    if confidence is None:
        confidence = 0

    mentioned_count = 0
    for _, row in ranked_rows.head(6).iterrows():
        if _already_covered_by_user_input(symptom, str(row.get("positive_keywords", ""))):
            mentioned_count += 1

    if text_len >= 35 and confidence >= 0.75 and mentioned_count >= 2:
        return 1

    if text_len >= 25 and confidence >= 0.65:
        return 2

    if text_len <= 10:
        return 4

    return 3


def _select_dynamic_questions(symptom: str, analysis: dict, limit: int = 4) -> list[TriageQuestion]:
    """
    모델이 예측한 suspected_disease를 기준으로 질문 후보를 넓게 가져온 뒤,
    질문별 점수를 계산해 필요한 질문만 선택한다.

    점수 요소:
    - 예측 질환 일치
    - 예측 증상군 일치
    - 위험도 점수
    - 질문 중요도
    - 사용자 입력에 이미 포함된 정보 패널티
    """
    disease_questions = load_disease_questions()
    selected: list[TriageQuestion] = []
    selected_ids: set[str] = set()

    if not disease_questions.empty:
        disease = str(analysis.get("suspected_disease", ""))
        disease_id = str(analysis.get("disease_id", ""))
        symptom_group = str(analysis.get("symptom_group", ""))

        if disease_id and "disease_id" in disease_questions.columns:
            disease_rows = disease_questions[
                disease_questions["disease_id"].astype(str).eq(disease_id)
            ].copy()
        else:
            disease_rows = pd.DataFrame()

        if disease_rows.empty:
            disease_rows = disease_questions[
                disease_questions["suspected_disease"].astype(str).eq(disease)
            ].copy()

        if not disease_rows.empty:
            candidate_rows = disease_rows
        else:
            candidate_rows = disease_questions[
                disease_questions["symptom_group"].astype(str).eq(symptom_group)
            ].copy()

        if candidate_rows.empty:
            candidate_rows = disease_questions.copy()

        candidate_rows["question_rank_score"] = candidate_rows.apply(
            lambda row: _score_question(row, symptom, analysis),
            axis=1,
        )

        candidate_rows = candidate_rows.sort_values(
            ["question_rank_score", "risk_score", "importance"],
            ascending=[False, False, False],
        )

        dynamic_limit = min(limit, _dynamic_question_limit(symptom, analysis, candidate_rows))

        for _, row in candidate_rows.iterrows():
            question_id = str(row["question_id"])
            if question_id in selected_ids:
                continue

            # 점수가 너무 낮은 group-only 질문은 제외
            if float(row["question_rank_score"]) < 12:
                continue

            # 사용자가 이미 명확히 말한 내용은 다시 묻지 않음
            if _already_covered_by_user_input(symptom, str(row.get("positive_keywords", ""))):
                continue

            selected.append(
                TriageQuestion(
                    id=question_id,
                    question=str(row["question"]),
                    options=["예", "아니오", "잘 모르겠음"],
                    allow_custom=False,
                )
            )
            selected_ids.add(question_id)

            if len(selected) >= dynamic_limit:
                break

    # 그래도 질문이 없으면 기존 응급도 룰에서 1개만 보강
    if len(selected) == 0:
        selected.extend(
            _select_fallback_triage_questions(
                symptom_group=str(analysis.get("symptom_group", "")),
                existing_question_ids=selected_ids,
                limit=1,
            )
        )

    return selected[:limit]


def _build_evidence(analysis: dict) -> AnalysisEvidence:
    matched_by = analysis.get("matched_by", "similarity")
    top_score = float(analysis.get("max_similarity", 0))

    if matched_by == "trained_classifier":
        explanation = (
            "네이버 지식인 증상 사례 데이터로 학습한 symptom_classifier.pkl 모델을 "
            "최우선으로 사용해 최종 증상군·진료과·의심질환을 예측했습니다. "
            "응급 문진 데이터는 질환 분류가 아니라 위험도 점수 계산에 보조적으로 사용했습니다."
        )
    elif matched_by == "similarity":
        explanation = (
            "학습 모델을 사용할 수 없어 네이버 지식인 실제 증상 사례와의 유사도 검색을 기반으로 추론했습니다."
        )
    else:
        explanation = (
            "네이버 기반 증상 분류 모델과 유사 사례 검색 결과를 결합해 분석했습니다."
        )

    return AnalysisEvidence(
        method=matched_by,
        model_used=bool(analysis.get("model_used", matched_by == "trained_classifier")),
        keyword_rule_used=bool(analysis.get("risk_rule_used", False)),
        similarity_top_score=round(top_score, 4),
        explanation=explanation,
    )


def _build_final_symptom_summary(symptom: str, answers) -> str:
    positives: list[str] = []
    uncertain: list[str] = []

    for item in answers:
        if item.answer == "예":
            positives.append(item.question)
        elif item.answer == "잘 모르겠음":
            uncertain.append(item.question)

    parts = [f"사용자 최초 증상: {symptom}"]

    if positives:
        parts.append("추가로 확인된 증상: " + " / ".join(positives))
    if uncertain:
        parts.append("불확실한 증상: " + " / ".join(uncertain))

    return " ".join(parts)


def create_data_driven_questions(symptom: str) -> dict:
    analysis = analyze_symptom_text(symptom)
    questions = _select_dynamic_questions(symptom=symptom, analysis=analysis, limit=4)

    return {
        "symptom": symptom,
        "symptom_group": analysis["symptom_group"],
        "department": analysis["department"],
        "suspected_disease": analysis["suspected_disease"],
        "disease_id": analysis.get("disease_id", ""),
        "canonical_disease_name": analysis.get("canonical_disease_name", analysis["suspected_disease"]),
        "disease_candidates": analysis.get("disease_candidates", []),
        "need_followup": len(questions) > 0,
        "questions": questions,
        "similar_cases": analysis["similar_cases"],
        "evidence": _build_evidence(analysis),
    }


def _answer_to_score(answer: str, rule_score: float) -> float:
    normalized = str(answer).strip().lower()

    if answer in YES_VALUES or normalized in YES_VALUES:
        return float(rule_score)
    if answer in UNKNOWN_VALUES or normalized in UNKNOWN_VALUES:
        return float(rule_score) * 0.4
    return 0.0


def _predict_severity_from_score(risk_score: float) -> int:
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
        score_map[str(row["question_id"])] = {
            "risk_score": float(row.get("risk_score", 0)),
            "required_resource_code": str(row.get("required_resource_code", "")),
        }

    for _, row in disease_questions.iterrows():
        score_map[str(row["question_id"])] = {
            "risk_score": float(row.get("risk_score", 0)),
            "required_resource_code": str(row.get("required_resource_code", "")),
        }

    return score_map


def analyze_data_driven_triage(payload: TriageAnalyzeRequest) -> TriageAnalyzeResponse:
    final_symptom_summary = _build_final_symptom_summary(payload.symptom, payload.answers)
    symptom_analysis = analyze_symptom_text(final_symptom_summary)
    question_score_map = _build_question_score_map()

    total_risk_score = 0.0
    matched_resource_codes: list[str] = []

    for answer in payload.answers:
        rule = question_score_map.get(answer.question_id)
        if not rule:
            continue

        rule_score = float(rule.get("risk_score", 0))
        added_score = _answer_to_score(answer.answer, rule_score)
        total_risk_score += added_score

        if added_score > 0:
            matched_resource_codes.append(str(rule.get("required_resource_code", "")))

    naver_level = int(symptom_analysis["naver_severity_level"])
    naver_based_risk = max(0, naver_level - 1)

    combined_risk_score = max(total_risk_score, naver_based_risk)
    combined_risk_score = min(10, combined_risk_score)
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
        f"네이버 지식인 증상 데이터 기반 학습 모델이 최종 증상을 분석한 결과 "
        f"{symptom_analysis['suspected_disease']} 가능성이 높고, "
        f"추천 진료과는 {symptom_analysis['department']}입니다. "
        f"응급 문진 데이터는 위험도 점수 계산에 보조적으로 사용했습니다."
    )

    return TriageAnalyzeResponse(
        final_symptom_summary=final_symptom_summary,
        severity_level=severity_level,
        severity_label=_severity_label(severity_level),
        risk_score=int(round(combined_risk_score)),
        required_resource_code=required_resource_code,
        symptom_group=symptom_analysis["symptom_group"],
        department=symptom_analysis["department"],
        suspected_disease=symptom_analysis["suspected_disease"],
        disease_id=symptom_analysis.get("disease_id", ""),
        canonical_disease_name=symptom_analysis.get(
            "canonical_disease_name",
            symptom_analysis["suspected_disease"],
        ),
        disease_candidates=symptom_analysis.get("disease_candidates", []),
        summary=summary,
        evidence=evidence,
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
        "toxic": "ER_GENERAL",
        "poisoning": "ER_GENERAL",
    }
    return mapping.get(symptom_group, "ER_GENERAL")
