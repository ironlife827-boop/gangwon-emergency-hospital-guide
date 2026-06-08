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
        "symptom_group": "poisoning",
        "department": "응급의학과",
        "suspected_disease": "중독",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["물에 빠", "익수", "잠겼", "호흡이 없", "숨을 안"],
        "symptom_group": "respiratory",
        "department": "응급의학과",
        "suspected_disease": "익수 또는 호흡부전",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["피가 멈추지", "출혈", "피를 많이", "피가 계속", "대량 출혈"],
        "symptom_group": "bleeding",
        "department": "응급의학과",
        "suspected_disease": "중증 출혈",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["의식이 없", "반응이 없", "깨워도", "쓰러졌", "기절"],
        "symptom_group": "neuro",
        "department": "응급의학과",
        "suspected_disease": "의식저하",
        "naver_severity_level": 5,
    },
    {
        "keywords": ["한쪽 팔", "한쪽 다리", "말이 어눌", "마비", "얼굴 비대칭"],
        "symptom_group": "neuro",
        "department": "신경과",
        "suspected_disease": "뇌졸중 의심",
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


def _find_keyword_override(symptom: str) -> dict | None:
    text = str(symptom).lower().replace(" ", "")

    for rule in EMERGENCY_KEYWORD_RULES:
        for keyword in rule["keywords"]:
            normalized_keyword = keyword.lower().replace(" ", "")
            if normalized_keyword in text:
                return rule

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


def analyze_symptom_text(symptom: str, top_k: int = 5) -> dict:
    cases = load_naver_cases()
    vectorizer, matrix = _get_vectorizer()

    query_vec = vectorizer.transform([symptom])
    sims = cosine_similarity(query_vec, matrix).ravel()

    top_indices = sims.argsort()[::-1][:top_k]
    top_rows = cases.iloc[top_indices].copy()
    top_rows["similarity"] = sims[top_indices]

    similar_cases = _build_similar_cases(top_rows)
    max_similarity = float(top_rows["similarity"].max()) if len(top_rows) else 0.0

    # 최종 정책:
    # 질환/진료과/증상군 추론은 네이버 지식인 사례로 학습한 모델을 우선 사용한다.
    # 응급 키워드 룰은 모델 파일이 없거나 예측 실패 시에만 안전장치로 사용한다.
    trained_prediction = _predict_with_trained_classifier(symptom)

    if trained_prediction is not None:
        naver_severity = int(round(float(top_rows["severity_level"].mean()))) if len(top_rows) else 1
        naver_severity = max(1, min(5, naver_severity))

        return {
            "symptom_group": trained_prediction["symptom_group"],
            "department": trained_prediction["department"],
            "suspected_disease": trained_prediction["suspected_disease"],
            "naver_severity_level": naver_severity,
            "max_similarity": round(max_similarity, 4),
            "similar_cases": similar_cases,
            "matched_by": "trained_classifier",
        }

    keyword_override = _find_keyword_override(symptom)

    if keyword_override is not None:
        return {
            "symptom_group": keyword_override["symptom_group"],
            "department": keyword_override["department"],
            "suspected_disease": keyword_override["suspected_disease"],
            "naver_severity_level": int(keyword_override["naver_severity_level"]),
            "max_similarity": round(max_similarity, 4),
            "similar_cases": similar_cases,
            "matched_by": "keyword_rule",
        }

    symptom_group = _majority_value(top_rows, "symptom_group", "etc")
    department = _majority_value(top_rows, "department", "내과")
    suspected_disease = _majority_value(top_rows, "suspected_disease", "일반 증상")

    naver_severity = int(round(float(top_rows["severity_level"].mean()))) if len(top_rows) else 1
    naver_severity = max(1, min(5, naver_severity))

    return {
        "symptom_group": symptom_group,
        "department": department,
        "suspected_disease": suspected_disease,
        "naver_severity_level": naver_severity,
        "max_similarity": round(max_similarity, 4),
        "similar_cases": similar_cases,
        "matched_by": "similarity",
    }
