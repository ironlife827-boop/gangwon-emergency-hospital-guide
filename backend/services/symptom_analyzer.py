from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schemas.triage import SimilarCase
from services.data_loader import load_naver_cases, load_symptom_classifier


_vectorizer: TfidfVectorizer | None = None
_matrix = None


# 질환 판단용이 아니라 위험도 보정용 안전장치
EMERGENCY_RISK_KEYWORD_RULES = [
    {"keywords": ["감전", "전기", "전류", "콘센트", "누전"], "risk_disease": "전기손상", "risk_severity_level": 5},
    {"keywords": ["화상", "데임", "데였", "끓는물", "뜨거운", "불에"], "risk_disease": "화상", "risk_severity_level": 4},
    {"keywords": ["중독", "약을 많이", "농약", "독극물", "화학물질", "세제", "락스"], "risk_disease": "화학물질중독", "risk_severity_level": 5},
    {"keywords": ["물에 빠", "익수", "잠겼", "호흡이 없", "숨을 안"], "risk_disease": "익수", "risk_severity_level": 5},
    {"keywords": ["피가 멈추지", "출혈", "피를 많이", "피가 계속", "대량 출혈"], "risk_disease": "대량출혈", "risk_severity_level": 5},
    {"keywords": ["의식이 없", "반응이 없", "깨워도", "쓰러졌", "기절"], "risk_disease": "심정지", "risk_severity_level": 5},
    {"keywords": ["한쪽 팔", "한쪽 다리", "말이 어눌", "마비", "얼굴 비대칭", "입이 한쪽"], "risk_disease": "뇌졸중", "risk_severity_level": 5},
    {"keywords": ["벌에쏘", "벌쏘", "벌침", "입술이붓", "얼굴이붓", "온몸이붓", "두드러기"], "risk_disease": "아나필락시스", "risk_severity_level": 5},
]


def _get_vectorizer():
    global _vectorizer, _matrix
    cases = load_naver_cases()

    if _vectorizer is None or _matrix is None:
        _vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=1,
        )
        _matrix = _vectorizer.fit_transform(cases["search_text"].astype(str).tolist())

    return _vectorizer, _matrix


def _majority_value(rows: pd.DataFrame, column: str, fallback: str = "기타") -> str:
    values = [str(value).strip() for value in rows[column].tolist() if str(value).strip()]
    if not values:
        return fallback
    return Counter(values).most_common(1)[0][0]


def _normalize_text(value: str) -> str:
    return str(value).lower().replace(" ", "").replace(",", "").replace(".", "")


def _find_emergency_risk_rule(symptom: str) -> dict | None:
    text = _normalize_text(symptom)

    for rule in EMERGENCY_RISK_KEYWORD_RULES:
        for keyword in rule["keywords"]:
            if _normalize_text(keyword) in text:
                return rule

    return None


def _predict_with_trained_classifier(symptom: str) -> dict | None:
    classifier = load_symptom_classifier()
    if classifier is None:
        return None

    try:
        symptom_group_model = classifier["symptom_group_model"]
        department_model = classifier["department_model"]
        disease_model = classifier["disease_model"]

        symptom_group = str(symptom_group_model.predict([symptom])[0])
        department = str(department_model.predict([symptom])[0])
        suspected_disease = str(disease_model.predict([symptom])[0])

        disease_confidence = None
        if hasattr(disease_model, "predict_proba"):
            disease_confidence = float(max(disease_model.predict_proba([symptom])[0]))

        return {
            "symptom_group": symptom_group,
            "department": department,
            "suspected_disease": suspected_disease,
            "disease_confidence": disease_confidence,
        }
    except Exception:
        return None


def _build_similar_cases(top_rows: pd.DataFrame) -> list[SimilarCase]:
    similar_cases = []

    for _, row in top_rows.iterrows():
        similar_cases.append(
            SimilarCase(
                case_id=int(row["case_id"]),
                cleaned_text=str(row["cleaned_text"]),
                symptom_group=str(row["symptom_group"]),
                department=str(row["department"]),
                suspected_disease=str(row["suspected_disease"]),
                severity_level=int(row["severity_level"]),
                similarity=round(float(row["similarity"]), 4),
                source_url=str(row.get("source_url", "")),
            )
        )

    return similar_cases


def _rank_rows_by_similarity(cases: pd.DataFrame, sims, candidate_mask, top_k: int) -> pd.DataFrame:
    candidate_indices = cases.index[candidate_mask].tolist()
    if not candidate_indices:
        return pd.DataFrame(columns=list(cases.columns) + ["similarity"])

    ranked_indices = sorted(candidate_indices, key=lambda idx: float(sims[idx]), reverse=True)[:top_k]
    rows = cases.loc[ranked_indices].copy()
    rows["similarity"] = [float(sims[idx]) for idx in ranked_indices]
    return rows


def _select_similar_case_rows(
    cases: pd.DataFrame,
    sims,
    predicted_disease: str,
    predicted_group: str,
    top_k: int,
) -> tuple[pd.DataFrame, str]:
    selected_parts: list[pd.DataFrame] = []
    used_indices: set[int] = set()
    search_scope = "disease"

    disease_mask = cases["suspected_disease"].astype(str).eq(str(predicted_disease))
    disease_rows = _rank_rows_by_similarity(cases, sims, disease_mask, top_k)
    selected_parts.append(disease_rows)
    used_indices.update(disease_rows.index.tolist())

    if sum(len(part) for part in selected_parts) < top_k:
        search_scope = "disease+group"
        remaining = top_k - sum(len(part) for part in selected_parts)
        group_mask = (
            cases["symptom_group"].astype(str).eq(str(predicted_group))
            & ~cases.index.isin(used_indices)
        )
        group_rows = _rank_rows_by_similarity(cases, sims, group_mask, remaining)
        selected_parts.append(group_rows)
        used_indices.update(group_rows.index.tolist())

    if sum(len(part) for part in selected_parts) < top_k:
        search_scope = "disease+group+fallback"
        remaining = top_k - sum(len(part) for part in selected_parts)
        fallback_mask = ~cases.index.isin(used_indices)
        fallback_rows = _rank_rows_by_similarity(cases, sims, fallback_mask, remaining)
        selected_parts.append(fallback_rows)

    selected = pd.concat([part for part in selected_parts if not part.empty], axis=0)
    return selected.head(top_k).copy(), search_scope


def _get_naver_severity_from_rows(rows: pd.DataFrame, fallback: int = 1) -> int:
    if rows.empty:
        return fallback

    value = int(round(float(rows["severity_level"].mean())))
    return max(1, min(5, value))


def analyze_symptom_text(symptom: str, top_k: int = 5) -> dict:
    cases = load_naver_cases()
    vectorizer, matrix = _get_vectorizer()

    query_vec = vectorizer.transform([symptom])
    sims = cosine_similarity(query_vec, matrix).ravel()

    # 1순위: 네이버 기반 학습 모델을 항상 먼저 사용
    trained_prediction = _predict_with_trained_classifier(symptom)

    if trained_prediction is not None:
        predicted = {
            "symptom_group": trained_prediction["symptom_group"],
            "department": trained_prediction["department"],
            "suspected_disease": trained_prediction["suspected_disease"],
        }
        matched_by = "trained_classifier"
        disease_confidence = trained_prediction.get("disease_confidence")
    else:
        # 모델이 없거나 로딩 실패한 경우에만 유사사례 fallback
        all_indices = sims.argsort()[::-1][:top_k]
        all_top_rows = cases.iloc[all_indices].copy()
        all_top_rows["similarity"] = sims[all_indices]

        predicted = {
            "symptom_group": _majority_value(all_top_rows, "symptom_group", "etc"),
            "department": _majority_value(all_top_rows, "department", "내과"),
            "suspected_disease": _majority_value(all_top_rows, "suspected_disease", "일반 증상"),
        }
        matched_by = "similarity"
        disease_confidence = None

    # 응급 키워드는 질환을 덮어쓰지 않고 위험도만 보정
    risk_rule = _find_emergency_risk_rule(symptom)

    top_rows, search_scope = _select_similar_case_rows(
        cases=cases,
        sims=sims,
        predicted_disease=predicted["suspected_disease"],
        predicted_group=predicted["symptom_group"],
        top_k=top_k,
    )

    similar_cases = _build_similar_cases(top_rows)
    max_similarity = float(top_rows["similarity"].max()) if len(top_rows) else 0.0

    model_based_severity = _get_naver_severity_from_rows(top_rows, fallback=1)

    if risk_rule is not None:
        naver_severity = max(model_based_severity, int(risk_rule["risk_severity_level"]))
        risk_rule_used = True
        risk_rule_disease = str(risk_rule["risk_disease"])
    else:
        naver_severity = model_based_severity
        risk_rule_used = False
        risk_rule_disease = ""

    return {
        "symptom_group": predicted["symptom_group"],
        "department": predicted["department"],
        "suspected_disease": predicted["suspected_disease"],
        "naver_severity_level": naver_severity,
        "max_similarity": round(max_similarity, 4),
        "similar_cases": similar_cases,
        "matched_by": matched_by,
        "model_used": trained_prediction is not None,
        "disease_confidence": None if disease_confidence is None else round(float(disease_confidence), 4),
        "risk_rule_used": risk_rule_used,
        "risk_rule_disease": risk_rule_disease,
        "similar_case_search_scope": search_scope,
    }
