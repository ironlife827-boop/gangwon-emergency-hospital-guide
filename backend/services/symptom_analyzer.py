from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schemas.triage import SimilarCase
from services.data_loader import load_naver_cases, load_symptom_classifier


_vectorizer: TfidfVectorizer | None = None
_matrix = None


EMERGENCY_KEYWORD_RULES = [
    {
        "keywords": ["감전", "전기", "전류", "콘센트", "누전"],
        "symptom_group": "trauma",
        "department": "응급의학과",
        "suspected_disease": "전기손상",
        "naver_severity_level": 4,
    },
    {
        "keywords": ["화상", "데임", "데였", "끓는물", "뜨거운", "불에"],
        "symptom_group": "trauma",
        "department": "응급의학과",
        "suspected_disease": "화상",
        "naver_severity_level": 4,
    },
    {
        "keywords": ["중독", "약을 많이", "농약", "독극물", "화학물질", "세제", "락스"],
        "symptom_group": "toxic",
        "department": "응급의학과",
        "suspected_disease": "화학물질중독",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["물에 빠", "익수", "잠겼", "호흡이 없", "숨을 안"],
        "symptom_group": "respiratory",
        "department": "응급의학과",
        "suspected_disease": "익수",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["피가 멈추지", "출혈", "피를 많이", "피가 계속", "대량 출혈"],
        "symptom_group": "bleeding",
        "department": "응급의학과",
        "suspected_disease": "대량출혈",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["의식이 없", "반응이 없", "깨워도", "쓰러졌", "기절"],
        "symptom_group": "cardio",
        "department": "응급의학과",
        "suspected_disease": "심정지",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["한쪽 팔", "한쪽 다리", "말이 어눌", "마비", "얼굴 비대칭"],
        "symptom_group": "neuro",
        "department": "신경과",
        "suspected_disease": "뇌졸중",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["벌에쏘", "벌쏘", "벌침", "입술이붓", "얼굴이붓", "온몸이붓", "두드러기"],
        "symptom_group": "allergy",
        "department": "알레르기내과",
        "suspected_disease": "아나필락시스",
        "naver_severity_level": 5,
    },
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


def _find_keyword_override(symptom: str) -> dict | None:
    text = _normalize_text(symptom)

    for rule in EMERGENCY_KEYWORD_RULES:
        for keyword in rule["keywords"]:
            normalized_keyword = _normalize_text(keyword)
            if normalized_keyword in text:
                return rule

    return None


def _predict_with_trained_classifier(symptom: str) -> dict | None:
    classifier = load_symptom_classifier()
    if classifier is None:
        return None

    try:
        symptom_group = str(classifier["symptom_group_model"].predict([symptom])[0])
        department = str(classifier["department_model"].predict([symptom])[0])
        suspected_disease = str(classifier["disease_model"].predict([symptom])[0])

        return {
            "symptom_group": symptom_group,
            "department": department,
            "suspected_disease": suspected_disease,
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


def _rank_rows_by_similarity(
    cases: pd.DataFrame,
    sims,
    candidate_mask,
    top_k: int,
) -> pd.DataFrame:
    candidate_indices = cases.index[candidate_mask].tolist()

    if not candidate_indices:
        return pd.DataFrame(columns=list(cases.columns) + ["similarity"])

    ranked_indices = sorted(
        candidate_indices,
        key=lambda idx: float(sims[idx]),
        reverse=True,
    )[:top_k]

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
    """
    기존 방식은 전체 2700건에서 바로 cosine top-k를 뽑았기 때문에,
    최종 질환은 맞아도 유사 사례가 다른 질환/낮은 유사도로 표시될 수 있었다.

    개선 방식:
    1. 예측 suspected_disease가 같은 사례 우선
    2. 부족하면 같은 symptom_group 사례
    3. 그래도 부족하면 전체 사례 fallback
    """
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

    selected = pd.concat(
        [part for part in selected_parts if not part.empty],
        axis=0,
    )

    selected = selected.head(top_k).copy()

    return selected, search_scope


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

    keyword_override = _find_keyword_override(symptom)
    trained_prediction = _predict_with_trained_classifier(symptom)

    if keyword_override is not None:
        predicted = {
            "symptom_group": keyword_override["symptom_group"],
            "department": keyword_override["department"],
            "suspected_disease": keyword_override["suspected_disease"],
        }
        matched_by = "keyword_rule"
        fallback_severity = int(keyword_override["naver_severity_level"])
    elif trained_prediction is not None:
        predicted = trained_prediction
        matched_by = "trained_classifier"
        fallback_severity = 1
    else:
        # 모델이 없을 때만 전체 유사도 기반으로 1차 예측한다.
        all_indices = sims.argsort()[::-1][:top_k]
        all_top_rows = cases.iloc[all_indices].copy()
        all_top_rows["similarity"] = sims[all_indices]

        predicted = {
            "symptom_group": _majority_value(all_top_rows, "symptom_group", "etc"),
            "department": _majority_value(all_top_rows, "department", "내과"),
            "suspected_disease": _majority_value(all_top_rows, "suspected_disease", "일반 증상"),
        }
        matched_by = "similarity"
        fallback_severity = _get_naver_severity_from_rows(all_top_rows, fallback=1)

    top_rows, search_scope = _select_similar_case_rows(
        cases=cases,
        sims=sims,
        predicted_disease=predicted["suspected_disease"],
        predicted_group=predicted["symptom_group"],
        top_k=top_k,
    )

    similar_cases = _build_similar_cases(top_rows)
    max_similarity = float(top_rows["similarity"].max()) if len(top_rows) else 0.0

    naver_severity = (
        int(keyword_override["naver_severity_level"])
        if keyword_override is not None
        else _get_naver_severity_from_rows(top_rows, fallback=fallback_severity)
    )

    return {
        "symptom_group": predicted["symptom_group"],
        "department": predicted["department"],
        "suspected_disease": predicted["suspected_disease"],
        "naver_severity_level": naver_severity,
        "max_similarity": round(max_similarity, 4),
        "similar_cases": similar_cases,
        "matched_by": matched_by,
        "similar_case_search_scope": search_scope,
    }
