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


DISEASE_ANCHOR_RULES = [
    {
        "disease": "전기손상",
        "risk_severity_level": 5,
        "priority": 30,
        "keyword_groups": [["감전", "전기", "전류", "콘센트", "누전"]],
    },
    {
        "disease": "뇌졸중",
        "risk_severity_level": 5,
        "keyword_groups": [
            ["한쪽", "왼팔", "오른팔", "편측", "마비"],
            ["힘이 안", "힘빠", "마비", "감각", "저림"],
            ["말이 어눌", "말이 안", "발음", "입이", "얼굴"],
        ],
    },
    {
        "disease": "뇌졸중",
        "risk_severity_level": 5,
        "priority": 28,
        "keyword_groups": [
            ["입꼬리", "얼굴", "안면", "눈"],
            ["처지", "감기지", "비대칭", "마비", "돌아가"],
            ["갑자기", "아침", "일어났", "한쪽"],
        ],
    },
    {
        "disease": "뇌졸중",
        "risk_severity_level": 5,
        "keyword_groups": [
            ["갑자기", "갑작", "깨질듯", "벼락"],
            ["두통", "머리"],
            ["구토", "토할", "어지럼", "의식"],
        ],
    },
    {
        "disease": "아나필락시스",
        "risk_severity_level": 5,
        "priority": 20,
        "keyword_groups": [
            ["벌", "쏘인", "쏘였", "음식", "약", "알레르기"],
            ["입술", "혀", "얼굴", "목", "붓", "두드러기"],
            ["숨쉬기", "숨이", "호흡곤란", "쌕쌕", "어지럼"],
        ],
    },
    {
        "disease": "급성 심근경색",
        "risk_severity_level": 5,
        "keyword_groups": [
            ["가슴", "흉통"],
            ["답답", "조이", "짓누", "통증", "숨이 차", "숨차"],
            ["식은땀", "왼팔", "호흡곤란", "숨차", "짓누"],
        ],
    },
    {
        "disease": "복막염",
        "risk_severity_level": 4,
        "keyword_groups": [
            ["배", "복부", "복통"],
            ["찢어질", "극심", "심하게", "칼로", "움직이면"],
            ["식은땀", "딱딱", "열", "구토"],
        ],
    },
    {
        "disease": "장폐색",
        "risk_severity_level": 4,
        "keyword_groups": [
            ["배", "복부", "복통"],
            ["팽만", "부풀", "가스", "대변", "변비"],
            ["구토", "토", "쥐어짜"],
        ],
    },
    {
        "disease": "위장관출혈",
        "risk_severity_level": 5,
        "keyword_groups": [["피토", "토혈", "검은변", "혈변", "커피색"]],
    },
    {
        "disease": "열사병",
        "risk_severity_level": 5,
        "keyword_groups": [
            ["더위", "폭염", "햇빛", "야외", "땡볕", "온열", "열사병"],
            ["고열", "열", "39도", "40도", "체온"],
            ["경련", "발작", "의식", "혼란", "쓰러"],
        ],
    },
    {
        "disease": "고열 동반 호흡곤란",
        "risk_severity_level": 5,
        "priority": 25,
        "keyword_groups": [
            ["고열", "열", "39도", "40도", "체온"],
            ["숨쉬", "숨이", "호흡곤란", "숨차", "숨찬", "숨을 못"],
        ],
    },
    {
        "disease": "노로바이러스 의심 급성 위장염",
        "risk_severity_level": 4,
        "priority": 35,
        "keyword_groups": [
            ["굴", "생굴", "조개", "해산물", "회"],
            ["구토", "토", "설사", "복통", "배아프", "메스꺼움"],
        ],
    },
    {
        "disease": "수막염 의심",
        "risk_severity_level": 5,
        "priority": 38,
        "keyword_groups": [
            ["고열", "열", "38도", "38.5", "39도", "40도", "오한"],
            ["두통", "머리"],
            ["심하게", "심한", "깨질", "진통제", "낫지", "목", "구토", "몸살", "쑤시"],
        ],
    },
    {
        "disease": "뇌진탕 의심 두부손상",
        "risk_severity_level": 5,
        "priority": 40,
        "keyword_groups": [
            ["머리", "두부", "뒤통수", "이마"],
            ["맞", "부딪", "떨어", "넘어", "사다리", "충격", "외상"],
            ["기절", "의식", "잠깐", "멍", "토", "구토", "어지럼"],
        ],
    },
    {
        "disease": "소아 고열 경련",
        "risk_severity_level": 5,
        "keyword_groups": [
            ["아이", "아기", "소아", "어린이", "애"],
            ["고열", "열", "39도", "40도", "체온"],
            ["경련", "발작", "몸을 떨", "눈이 돌아"],
        ],
    },
    {
        "disease": "탈수",
        "risk_severity_level": 4,
        "keyword_groups": [
            ["토", "구토", "설사", "물설사"],
            ["탈수", "소변", "입마름", "어지럼", "기운", "축"],
        ],
    },
    {
        "disease": "기도폐쇄",
        "risk_severity_level": 5,
        "priority": 20,
        "keyword_groups": [
            ["목에걸", "기도", "음식", "이물", "사레", "걸렸", "막혔"],
            ["숨", "말", "막힘", "못쉬", "청색증", "켁켁"],
        ],
    },
    {
        "disease": "익수",
        "risk_severity_level": 5,
        "priority": 30,
        "keyword_groups": [["물에 빠", "익수", "물 삼", "수영"], ["숨", "기침", "의식", "구조"]],
    },
    {
        "disease": "약물중독",
        "risk_severity_level": 5,
        "priority": 20,
        "keyword_groups": [["약", "수면제", "진통제", "복용"], ["많이", "과다", "여러", "자살", "의식"]],
    },
    {
        "disease": "화학물질중독",
        "risk_severity_level": 5,
        "priority": 20,
        "keyword_groups": [["락스", "세제", "농약", "화학물질", "가스"], ["마셨", "흡입", "눈", "피부", "숨"]],
    },
    {
        "disease": "독사교상",
        "risk_severity_level": 5,
        "keyword_groups": [["뱀", "독사", "물렸"], ["붓", "통증", "어지럼", "구토"]],
    },
    {
        "disease": "벌쏘임",
        "risk_severity_level": 3,
        "keyword_groups": [["벌", "벌침", "쏘인", "쏘였"]],
    },
    {
        "disease": "급성 시력상실",
        "risk_severity_level": 4,
        "keyword_groups": [["눈", "시야", "시력"], ["안보", "흐려", "상실", "번쩍"]],
    },
]


DISEASE_EVIDENCE_RULES = [
    {"disease": "감기", "priority": 18, "keyword_groups": [["목", "인후", "목아"], ["콧물", "코막힘", "재채기"], ["기침"]]},
    {"disease": "독감", "priority": 26, "keyword_groups": [["39도", "고열", "열"], ["몸살", "근육통", "쑤시", "오한", "지속", "계속"], ["기침", "해열제", "이틀", "안떨어"]]},
    {"disease": "코로나19", "priority": 26, "keyword_groups": [["열", "기침"], ["냄새", "후각", "맛", "미각"]]},
    {"disease": "편도염", "priority": 22, "keyword_groups": [["목", "인후", "편도"], ["침삼", "삼키기", "삼킬"], ["힘들", "아프"]]},
    {"disease": "기관지염", "priority": 20, "keyword_groups": [["기침"], ["2주", "오래", "계속"], ["가래"]]},
    {"disease": "폐렴", "priority": 28, "keyword_groups": [["고열", "열"], ["기침", "가래"], ["가슴", "흉통", "숨차", "숨이차"]]},
    {"disease": "천식", "priority": 26, "keyword_groups": [["숨", "호흡"], ["쌕쌕", "천명", "휘파람"]]},
    {"disease": "알레르기 비염", "priority": 20, "keyword_groups": [["재채기"], ["콧물", "코막힘"], ["가렵", "알레르기"]]},
    {"disease": "중이염", "priority": 20, "keyword_groups": [["귀"], ["아프", "통증", "먹먹"], ["잘들리지", "청력", "들리지"]]},
    {"disease": "결막염", "priority": 20, "keyword_groups": [["눈"], ["충혈", "빨갛"], ["눈곱", "가렵", "눈물"]]},
    {"disease": "편두통", "priority": 21, "keyword_groups": [["한쪽"], ["머리", "두통"], ["욱신", "빛", "구역"]]},
    {"disease": "긴장성 두통", "priority": 18, "keyword_groups": [["머리", "두통"], ["띠", "조여", "압박"]]},
    {"disease": "뇌수막염", "priority": 34, "keyword_groups": [["고열", "열"], ["두통", "머리"], ["목", "뻣뻣", "구토", "빛"]]},
    {"disease": "치매 초기", "priority": 16, "keyword_groups": [["기억", "건망"], ["최근", "자꾸", "반복"]]},
    {"disease": "공황장애", "priority": 20, "keyword_groups": [["갑자기", "발작"], ["심장", "두근"], ["숨", "불안", "공포"]]},
    {"disease": "우울증", "priority": 16, "keyword_groups": [["우울"], ["무기력", "하기싫", "흥미"]]},
    {"disease": "불면증", "priority": 16, "keyword_groups": [["잠"], ["어렵", "못자", "깨"]]},
    {"disease": "역류성 식도염", "priority": 20, "keyword_groups": [["속", "가슴"], ["신물", "역류", "트림"]]},
    {"disease": "위염", "priority": 18, "keyword_groups": [["명치", "속"], ["쓰리", "불편", "소화"]]},
    {"disease": "위궤양", "priority": 21, "keyword_groups": [["식사", "식후"], ["명치", "속"], ["통증", "쓰림"]]},
    {"disease": "장염", "priority": 30, "keyword_groups": [["설사", "물설사"], ["복통", "배아", "배가아", "배"], ["6번", "여러", "계속", "반복", "구토", "열"]]},
    {"disease": "과민성대장증후군", "priority": 18, "keyword_groups": [["긴장", "스트레스"], ["배", "복통"], ["설사", "변비"]]},
    {"disease": "맹장염", "priority": 32, "keyword_groups": [["오른쪽아랫배", "우하복부", "맹장", "충수"], ["아프", "통증"], ["걷", "미열", "구역", "심해"]]},
    {"disease": "담석증", "priority": 24, "keyword_groups": [["오른쪽윗배", "우상복부"], ["구역", "메스꺼", "기름"], ["아프", "통증"]]},
    {"disease": "간염", "priority": 22, "keyword_groups": [["피부", "눈"], ["노랗", "황달"], ["피로", "소변"]]},
    {"disease": "신장결석", "priority": 24, "keyword_groups": [["옆구리"], ["찢어질", "극심", "통증"], ["혈뇨", "소변", "구역"]]},
    {"disease": "방광염", "priority": 20, "keyword_groups": [["소변"], ["따갑", "통증"], ["자주", "마렵", "빈뇨"]]},
    {"disease": "요로감염", "priority": 22, "keyword_groups": [["열", "오한"], ["소변", "배뇨"], ["통증", "따갑", "옆구리"]]},
    {"disease": "전립선염", "priority": 20, "keyword_groups": [["회음부", "골반"], ["배뇨", "소변"], ["불편", "통증"]]},
    {"disease": "당뇨병", "priority": 18, "keyword_groups": [["물", "갈증"], ["소변"], ["많이", "자주"]]},
    {"disease": "저혈당", "priority": 24, "keyword_groups": [["식은땀"], ["손", "떨", "어지", "기운", "혈당"]]},
    {"disease": "갑상선 기능 항진증", "priority": 18, "keyword_groups": [["심장", "두근", "빨리"], ["체중", "줄"], ["손떨", "더위"]]},
    {"disease": "갑상선 기능 저하증", "priority": 18, "keyword_groups": [["피곤"], ["체중", "늘"], ["추위", "붓"]]},
    {"disease": "고혈압", "priority": 18, "keyword_groups": [["뒷목", "혈압"], ["당기", "두통", "아프"]]},
    {"disease": "협심증", "priority": 24, "keyword_groups": [["운동", "걸을"], ["가슴", "흉통"], ["조이", "답답"]]},
    {"disease": "심근경색", "priority": 34, "keyword_groups": [["가슴", "흉통"], ["짓누", "쥐어짜", "답답"], ["식은땀", "왼팔", "숨차"]]},
    {"disease": "부정맥", "priority": 24, "keyword_groups": [["심장", "맥박"], ["불규칙", "두근", "건너"]]},
    {"disease": "심부전", "priority": 24, "keyword_groups": [["조금만", "누우면", "걸어도"], ["숨", "숨차"], ["다리", "부종", "피로"]]},
    {"disease": "아토피", "priority": 18, "keyword_groups": [["피부"], ["가렵"], ["붉", "건조", "습진"]]},
    {"disease": "두드러기", "priority": 20, "keyword_groups": [["피부"], ["발진", "두드러기"], ["갑자기", "가렵", "붉"]]},
    {"disease": "대상포진", "priority": 22, "keyword_groups": [["한쪽"], ["물집", "수포"], ["통증", "화끈"]]},
    {"disease": "무좀", "priority": 18, "keyword_groups": [["발가락", "발"], ["사이"], ["가렵", "벗겨", "진물"]]},
    {"disease": "류마티스 관절염", "priority": 20, "keyword_groups": [["아침"], ["손가락", "관절"], ["뻣뻣", "붓"]]},
    {"disease": "통풍", "priority": 22, "keyword_groups": [["엄지발가락", "발가락"], ["붓", "빨갛"], ["극심", "아프", "통증"]]},
    {"disease": "디스크", "priority": 20, "keyword_groups": [["허리"], ["다리"], ["저리", "통증"]]},
    {"disease": "오십견", "priority": 18, "keyword_groups": [["어깨"], ["팔"], ["안올라", "못올", "아프"]]},
    {"disease": "골절", "priority": 22, "keyword_groups": [["넘어", "다쳤", "부딪", "뚝", "소리"], ["팔", "다리", "무릎", "발목", "손목"], ["붓", "움직일", "걷기힘", "체중"]]},
    {"disease": "빈혈", "priority": 18, "keyword_groups": [["어지"], ["피곤", "창백", "숨차"]]},
    {"disease": "패혈증 의심", "priority": 34, "keyword_groups": [["고열", "열"], ["의식", "혼돈", "축", "저하"]]},
    {"disease": "아나필락시스", "priority": 36, "keyword_groups": [["음식", "약", "벌"], ["입술", "얼굴", "혀", "목", "두드러기"], ["숨", "호흡", "어지럼"]]},
]


SAFETY_ANCHOR_METADATA = {
    "소아 고열 경련": {
        "symptom_group": "pediatric",
        "department": "응급의학과",
        "suspected_disease": "소아 고열 경련",
    },
    "탈수": {
        "symptom_group": "abdominal",
        "department": "응급의학과",
        "suspected_disease": "탈수",
    },
    "고열 동반 호흡곤란": {
        "symptom_group": "respiratory",
        "department": "응급의학과",
        "suspected_disease": "고열 동반 호흡곤란",
    },
    "노로바이러스 의심 급성 위장염": {
        "symptom_group": "abdominal",
        "department": "소화기내과",
        "suspected_disease": "노로바이러스 의심 급성 위장염",
    },
    "뇌진탕 의심 두부손상": {
        "symptom_group": "trauma",
        "department": "응급의학과",
        "suspected_disease": "뇌진탕 의심 두부손상",
    },
}


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


def _keyword_group_matches(text: str, keywords: list[str]) -> tuple[bool, int]:
    hits = sum(1 for keyword in keywords if _normalize_text(keyword) in text)
    return hits > 0, hits


def _find_disease_anchor_rule(symptom: str) -> dict | None:
    text = _normalize_text(symptom)
    best_rule = None
    best_score = 0

    for rule in DISEASE_ANCHOR_RULES:
        score = int(rule.get("priority", 0))
        all_groups_matched = True

        for keyword_group in rule["keyword_groups"]:
            matched, hits = _keyword_group_matches(text, keyword_group)
            if not matched:
                all_groups_matched = False
                break
            score += 10 + hits

        if all_groups_matched and score > best_score:
            best_rule = rule
            best_score = score

    if best_rule is None:
        return None

    return {**best_rule, "anchor_score": best_score}


def _find_disease_evidence_rule(symptom: str) -> dict | None:
    text = _normalize_text(symptom)
    best_rule = None
    best_score = 0

    for rule in DISEASE_EVIDENCE_RULES:
        score = int(rule.get("priority", 0))
        all_groups_matched = True

        for keyword_group in rule["keyword_groups"]:
            matched, hits = _keyword_group_matches(text, keyword_group)
            if not matched:
                all_groups_matched = False
                break
            score += 8 + hits

        if all_groups_matched and score > best_score:
            best_rule = rule
            best_score = score

    if best_rule is None:
        return None

    return {**best_rule, "evidence_score": best_score}


def _metadata_for_disease(cases: pd.DataFrame, disease: str) -> dict | None:
    disease_rows = cases[cases["suspected_disease"].astype(str).eq(str(disease))]
    if disease_rows.empty:
        return SAFETY_ANCHOR_METADATA.get(str(disease))

    return {
        "symptom_group": _majority_value(disease_rows, "symptom_group"),
        "department": _majority_value(disease_rows, "department"),
        "suspected_disease": str(disease),
    }


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


ANIMAL_CASE_KEYWORDS = [
    "강아지",
    "고양이",
    "반려견",
    "반려묘",
    "햄스터",
    "동물병원",
    "사료",
    "우리집개",
    "개가",
    "개는",
    "강아지가",
    "고양이가",
]


def _human_case_mask(cases: pd.DataFrame) -> pd.Series:
    normalized = cases["cleaned_text"].fillna("").astype(str).map(_normalize_text)
    animal_pattern = "|".join(ANIMAL_CASE_KEYWORDS)
    return ~normalized.str.contains(animal_pattern, regex=True)


def _rank_rows_by_similarity(cases: pd.DataFrame, sims, candidate_mask, top_k: int) -> pd.DataFrame:
    human_mask = _human_case_mask(cases)
    candidate_indices = cases.index[candidate_mask & human_mask].tolist()
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
    if disease_rows.empty and str(predicted_disease) in SAFETY_ANCHOR_METADATA:
        return pd.DataFrame(columns=list(cases.columns) + ["similarity"]), "safety_anchor_no_case"

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
        disease_metadata = _metadata_for_disease(cases, predicted["suspected_disease"])
        if disease_metadata is not None:
            predicted["symptom_group"] = disease_metadata["symptom_group"]
            predicted["department"] = disease_metadata["department"]
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

    risk_rule = _find_emergency_risk_rule(symptom)
    anchor_rule = _find_disease_anchor_rule(symptom)
    evidence_rule = _find_disease_evidence_rule(symptom)

    # classifier 신뢰도가 낮고 고위험 앵커 증상이 명확하면,
    # triage 룰이 아니라 네이버 사례 데이터의 동일 질환 메타데이터로만 보정한다.
    if evidence_rule is not None:
        should_use_evidence = (
            disease_confidence is None
            or disease_confidence < 0.45
            or str(evidence_rule["disease"]) == str(predicted["suspected_disease"])
            or int(evidence_rule["evidence_score"]) >= 55
        )
        if should_use_evidence:
            evidence_prediction = _metadata_for_disease(cases, str(evidence_rule["disease"]))
            if evidence_prediction is not None:
                predicted = evidence_prediction
                matched_by = "trained_classifier_evidence"

    if risk_rule is not None and (disease_confidence is None or disease_confidence < 0.5):
        anchored_prediction = _metadata_for_disease(cases, str(risk_rule["risk_disease"]))
        if anchored_prediction is not None:
            predicted = anchored_prediction
            matched_by = "trained_classifier_anchor"

    if anchor_rule is not None:
        should_anchor = (
            disease_confidence is None
            or disease_confidence < 0.55
            or str(anchor_rule["disease"]) == str(predicted["suspected_disease"])
        )
        if should_anchor:
            anchored_prediction = _metadata_for_disease(cases, str(anchor_rule["disease"]))
            if anchored_prediction is not None:
                predicted = anchored_prediction
                matched_by = "trained_classifier_anchor"

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

    if risk_rule is not None or anchor_rule is not None:
        risk_level_candidates = [model_based_severity]
        if risk_rule is not None:
            risk_level_candidates.append(int(risk_rule["risk_severity_level"]))
        if anchor_rule is not None and str(anchor_rule["disease"]) == str(predicted["suspected_disease"]):
            risk_level_candidates.append(int(anchor_rule["risk_severity_level"]))

        naver_severity = max(risk_level_candidates)
        risk_rule_used = True
        risk_rule_disease = str(
            risk_rule["risk_disease"] if risk_rule is not None else anchor_rule["disease"]
        )
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
        "anchor_rule_disease": "" if anchor_rule is None else str(anchor_rule["disease"]),
        "anchor_rule_score": 0 if anchor_rule is None else int(anchor_rule["anchor_score"]),
        "evidence_rule_disease": "" if evidence_rule is None else str(evidence_rule["disease"]),
        "evidence_rule_score": 0 if evidence_rule is None else int(evidence_rule["evidence_score"]),
        "similar_case_search_scope": search_scope,
    }
