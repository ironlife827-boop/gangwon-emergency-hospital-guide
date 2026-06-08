from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schemas.triage import SimilarCase
from services.data_loader import load_naver_cases


_vectorizer: TfidfVectorizer | None = None
_matrix = None


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


def analyze_symptom_text(symptom: str, top_k: int = 5) -> dict:
    cases = load_naver_cases()
    vectorizer, matrix = _get_vectorizer()

    query_vec = vectorizer.transform([symptom])
    sims = cosine_similarity(query_vec, matrix).ravel()

    top_indices = sims.argsort()[::-1][:top_k]
    top_rows = cases.iloc[top_indices].copy()
    top_rows["similarity"] = sims[top_indices]

    # 너무 낮은 유사도만 나온 경우에도 최상위 결과는 사용하되, 신뢰도 표시용으로 남긴다.
    symptom_group = _majority_value(top_rows, "symptom_group", "etc")
    department = _majority_value(top_rows, "department", "내과")
    suspected_disease = _majority_value(top_rows, "suspected_disease", "일반 증상")

    # 네이버 데이터 기준 severity_level은 숫자가 클수록 위험하다고 간주한다.
    naver_severity = int(round(float(top_rows["severity_level"].mean()))) if len(top_rows) else 1
    naver_severity = max(1, min(5, naver_severity))

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
            )
        )

    max_similarity = float(top_rows["similarity"].max()) if len(top_rows) else 0.0

    return {
        "symptom_group": symptom_group,
        "department": department,
        "suspected_disease": suspected_disease,
        "naver_severity_level": naver_severity,
        "max_similarity": round(max_similarity, 4),
        "similar_cases": similar_cases,
    }
