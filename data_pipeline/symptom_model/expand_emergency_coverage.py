from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
LABEL_MASTER_PATH = DATA_DIR / "emergency_disease_label_master.csv"
QUERY_PLAN_PATH = DATA_DIR / "naver_crawl_query_plan.csv"
QUESTION_MAP_PATH = DATA_DIR / "disease_question_map.csv"
TRIAGE_RULE_PATH = DATA_DIR / "triage_rule_dataset.csv"

QUESTION_COLUMNS = [
    "question_id",
    "suspected_disease",
    "symptom_group",
    "question",
    "positive_keywords",
    "risk_score",
    "required_resource_code",
    "importance",
]
TRIAGE_COLUMNS = [
    "symptom_group",
    "question_id",
    "question",
    "answer_option",
    "risk_score",
    "suspected_disease",
    "required_resource_code",
]

LABELS = [
    ("뇌진탕 의심 두부손상", "trauma", "응급의학과", 5, "머리 맞음;두부외상;기절;의식소실;구토;사다리 추락"),
    ("외상성 뇌손상", "trauma", "응급의학과", 5, "두부손상;의식저하;반복구토;두통악화;두개골골절"),
    ("경추손상", "trauma", "응급의학과", 5, "목 다침;목 통증;팔다리 마비;추락;교통사고"),
    ("척추손상", "trauma", "응급의학과", 5, "허리 외상;감각저하;마비;대소변장애;추락"),
    ("다발성외상", "trauma", "응급의학과", 5, "교통사고;추락;여러 부위 손상;의식저하;출혈"),
    ("개방성 골절", "trauma", "정형외과", 5, "뼈 보임;개방성 골절;출혈;변형;극심한 통증"),
    ("절단손상", "trauma", "응급의학과", 5, "손가락 절단;발가락 절단;절단;압궤;출혈"),
    ("압궤손상", "trauma", "응급의학과", 5, "끼임;눌림;압궤;붓기;감각저하"),
    ("안면외상", "trauma", "응급의학과", 4, "얼굴 다침;코피;턱 통증;시야 이상;치아 손상"),
    ("고열 동반 호흡곤란", "respiratory", "응급의학과", 5, "40도 열;고열;숨쉬기 힘듦;호흡곤란;청색증"),
    ("폐렴 의심 고열", "respiratory", "호흡기내과", 4, "고열;기침;가래;숨참;흉통"),
    ("천식 악화", "respiratory", "호흡기내과", 5, "천식;쌕쌕;흡입기;숨참;말하기 어려움"),
    ("COPD 급성악화", "respiratory", "호흡기내과", 5, "만성폐질환;가래 증가;숨참;청색증;산소"),
    ("기흉", "respiratory", "호흡기내과", 5, "갑작스런 흉통;숨참;한쪽 가슴;마른체형;호흡곤란"),
    ("폐색전증", "respiratory", "응급의학과", 5, "갑작스런 숨참;흉통;다리부종;수술후;장거리 이동"),
    ("급성 심부전", "cardio", "심장내과", 5, "숨참;누우면 악화;다리부종;거품가래;심부전"),
    ("대동맥박리", "cardio", "응급의학과", 5, "찢어지는 흉통;등 통증;혈압차;실신;대동맥"),
    ("고혈압성 응급", "cardio", "응급의학과", 5, "혈압 180;심한 두통;흉통;시야 이상;신경증상"),
    ("실신", "neuro", "응급의학과", 4, "기절;쓰러짐;의식소실;어지럼;회복"),
    ("경련 발작", "neuro", "신경과", 5, "경련;발작;거품;의식저하;반복"),
    ("수막염 의심", "neuro", "응급의학과", 5, "고열;목 뻣뻣;두통;구토;의식저하"),
    ("편두통 위험징후", "neuro", "신경과", 3, "두통;시야번쩍;구토;편측;반복"),
    ("급성 충수염", "abdominal", "외과", 4, "오른쪽 아랫배;복통;열;구토;눌렀다 뗄 때 통증"),
    ("담낭염", "abdominal", "소화기내과", 4, "오른쪽 윗배;열;구토;기름진 음식;황달"),
    ("요로결석", "urology", "비뇨의학과", 4, "옆구리 통증;혈뇨;구토;소변통;극심한 통증"),
    ("급성 신우신염", "urology", "비뇨의학과", 4, "고열;옆구리 통증;소변통;오한;혈뇨"),
    ("고환염전", "urology", "비뇨의학과", 5, "고환통;갑작스런 통증;붓기;구토;청소년"),
    ("노로바이러스 의심 급성 위장염", "abdominal", "소화기내과", 4, "굴;생굴;해산물;구토;설사;복통;오한"),
    ("식중독", "abdominal", "소화기내과", 4, "상한 음식;구토;설사;복통;열"),
    ("중증 탈수", "abdominal", "응급의학과", 5, "소변감소;입마름;어지럼;반복구토;설사"),
    ("저혈당", "toxic", "응급의학과", 5, "당뇨;식은땀;손떨림;의식저하;혈당 낮음"),
    ("고혈당성 응급", "toxic", "응급의학과", 5, "당뇨;혈당 높음;구토;복통;의식저하"),
    ("패혈증 의심", "infection", "응급의학과", 5, "고열;저체온;의식저하;호흡빠름;혈압저하"),
    ("열성경련", "pediatric", "소아청소년과", 5, "아이 고열;경련;발작;의식;반복"),
    ("영아 호흡곤란", "pediatric", "소아청소년과", 5, "아기;숨참;쌕쌕;청색증;수유곤란"),
    ("소아 탈수", "pediatric", "소아청소년과", 4, "아이 설사;구토;소변감소;눈물없음;축 처짐"),
    ("임신 중 복통출혈", "obgy", "산부인과", 5, "임신;복통;질출혈;어지럼;태동감소"),
    ("자궁외임신 의심", "obgy", "산부인과", 5, "임신초기;아랫배통증;질출혈;어지럼;실신"),
    ("분만 임박", "obgy", "산부인과", 5, "진통;양수;출산;규칙적 통증;임신"),
    ("자살위험", "psychiatric", "정신건강의학과", 5, "자살;죽고싶다;약 먹음;자해;유서"),
    ("공황발작", "psychiatric", "정신건강의학과", 3, "공황;숨막힘;두근거림;죽을 것 같음;불안"),
    ("섬망 의심", "psychiatric", "응급의학과", 4, "갑자기 이상행동;혼돈;고령;의식변화;환각"),
    ("눈 화학손상", "eye", "안과", 5, "락스 눈;화학물질 눈;눈 통증;시야 이상;세척"),
    ("망막박리 의심", "eye", "안과", 4, "번쩍임;날파리;시야 가림;갑작스런 시력저하;커튼"),
    ("각막손상", "eye", "안과", 4, "눈 찔림;이물감;통증;눈물;시야흐림"),
    ("기도 이물", "foreign_body", "응급의학과", 5, "목에 걸림;음식물;말 못함;기침 못함;청색증"),
    ("식도 이물", "foreign_body", "이비인후과", 4, "삼킴곤란;생선가시;목통증;침흘림;흉통"),
    ("아나필락시스", "allergy", "알레르기내과", 5, "두드러기;입술부음;숨참;어지럼;벌쏘임"),
    ("혈관부종", "allergy", "알레르기내과", 5, "입술부음;혀부음;목조임;약물;알레르기"),
    ("저체온증", "toxic", "응급의학과", 5, "추위노출;떨림;의식저하;체온저하;젖은 옷"),
    ("열사병", "toxic", "응급의학과", 5, "더위;고온;의식혼란;고열;땀 안남"),
    ("일산화탄소중독", "toxic", "응급의학과", 5, "연탄;보일러;두통;어지럼;여러명 증상"),
    ("화학물질중독", "toxic", "응급의학과", 5, "락스;농약;세제;흡입;구토"),
    ("알코올중독", "toxic", "응급의학과", 4, "술;의식저하;구토;호흡느림;만취"),
]

GROUP_RESOURCE = {
    "cardio": "ER_CARDIO",
    "neuro": "ER_NEURO",
    "respiratory": "ER_RESP",
    "trauma": "ER_TRAUMA",
    "abdominal": "ER_GENERAL",
    "urology": "ER_GENERAL",
    "pediatric": "ER_PED",
    "obgy": "ER_OBGY",
    "eye": "ER_GENERAL",
    "allergy": "ER_GENERAL",
    "toxic": "ER_GENERAL",
    "infection": "ER_GENERAL",
    "psychiatric": "ER_GENERAL",
    "foreign_body": "ER_GENERAL",
}


def _label_code(index: int) -> str:
    return f"EXP{index:03d}"


def _question_rows(index: int, label: tuple[str, str, str, int, str]) -> list[dict[str, str | int]]:
    disease, group, _department, severity, keywords = label
    safe_id = _label_code(index)
    keyword_parts = keywords.split(";")
    first_keywords = ";".join(keyword_parts[:4])
    resource = GROUP_RESOURCE.get(group, "ER_GENERAL")
    base_score = 5 if severity >= 5 else 4

    return [
        {
            "question_id": f"DQ_EXP_{safe_id}_001",
            "suspected_disease": disease,
            "symptom_group": group,
            "question": f"{disease}와 관련된 핵심 증상이 갑자기 시작됐나요?",
            "positive_keywords": first_keywords,
            "risk_score": base_score,
            "required_resource_code": resource,
            "importance": 5,
        },
        {
            "question_id": f"DQ_EXP_{safe_id}_002",
            "suspected_disease": disease,
            "symptom_group": group,
            "question": "의식 저하, 실신, 심한 어지럼이 함께 있나요?",
            "positive_keywords": "의식저하;실신;기절;어지럼",
            "risk_score": 5,
            "required_resource_code": resource,
            "importance": 5,
        },
        {
            "question_id": f"DQ_EXP_{safe_id}_003",
            "suspected_disease": disease,
            "symptom_group": group,
            "question": "통증이나 증상이 점점 심해지고 있나요?",
            "positive_keywords": "악화;심해짐;극심한통증;지속",
            "risk_score": base_score,
            "required_resource_code": resource,
            "importance": 4,
        },
        {
            "question_id": f"DQ_EXP_{safe_id}_004",
            "suspected_disease": disease,
            "symptom_group": group,
            "question": "구토, 고열, 식은땀, 창백함 중 하나라도 동반되나요?",
            "positive_keywords": "구토;고열;식은땀;창백",
            "risk_score": base_score,
            "required_resource_code": resource,
            "importance": 4,
        },
        {
            "question_id": f"DQ_EXP_{safe_id}_005",
            "suspected_disease": disease,
            "symptom_group": group,
            "question": "영유아, 고령자, 임산부이거나 심장·폐·당뇨 기저질환이 있나요?",
            "positive_keywords": "영유아;고령;임산부;기저질환;당뇨",
            "risk_score": 3,
            "required_resource_code": resource,
            "importance": 3,
        },
    ]


def _read_existing_questions() -> tuple[list[dict[str, str]], set[str], set[str]]:
    if not QUESTION_MAP_PATH.exists():
        return [], set(), set()

    with QUESTION_MAP_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    question_ids = {row["question_id"] for row in rows}
    diseases = {row["suspected_disease"] for row in rows}
    return rows, question_ids, diseases


def write_label_master() -> None:
    with LABEL_MASTER_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["suspected_disease", "symptom_group", "department", "severity_level", "search_keywords"])
        for label in LABELS:
            writer.writerow(label)


def write_query_plan() -> None:
    with QUERY_PLAN_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["suspected_disease", "query", "target_count"])
        for disease, _group, _department, _severity, keywords in LABELS:
            for keyword in keywords.split(";"):
                writer.writerow([disease, f"{keyword} 응급실 증상", 30])
            writer.writerow([disease, f"{disease} 증상 응급", 30])


def expand_question_map() -> None:
    rows, question_ids, diseases = _read_existing_questions()
    generated_diseases = {label[0] for label in LABELS}
    rows = [
        row
        for row in rows
        if not (
            row.get("suspected_disease") in generated_diseases
            and str(row.get("question_id", "")).startswith("DQ_EXP_")
        )
    ]
    question_ids = {row["question_id"] for row in rows}
    diseases = {
        row["suspected_disease"]
        for row in rows
        if not str(row.get("question_id", "")).startswith("DQ_EXP_")
    }

    for index, label in enumerate(LABELS, start=1):
        disease = label[0]
        if disease in diseases:
            continue

        for row in _question_rows(index, label):
            if row["question_id"] in question_ids:
                continue
            rows.append({column: str(row[column]) for column in QUESTION_COLUMNS})
            question_ids.add(str(row["question_id"]))

    with QUESTION_MAP_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUESTION_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def expand_triage_rules() -> None:
    if TRIAGE_RULE_PATH.exists():
        with TRIAGE_RULE_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        rows = []

    generated_diseases = {label[0] for label in LABELS}
    rows = [
        row
        for row in rows
        if not (
            row.get("suspected_disease") in generated_diseases
            and str(row.get("question_id", "")).startswith("TRIAGE_EXP_")
        )
    ]
    existing_ids = {row["question_id"] for row in rows}

    for index, (disease, group, _department, severity, keywords) in enumerate(LABELS, start=1):
        safe_id = _label_code(index)
        question_id = f"TRIAGE_EXP_{safe_id}_001"
        if question_id in existing_ids:
            continue

        rows.append(
            {
                "symptom_group": group,
                "question_id": question_id,
                "question": f"{disease} 관련 고위험 증상이 있습니까?",
                "answer_option": "예",
                "risk_score": str(5 if severity >= 5 else 4),
                "suspected_disease": disease,
                "required_resource_code": GROUP_RESOURCE.get(group, "ER_GENERAL"),
            }
        )
        existing_ids.add(question_id)

    with TRIAGE_RULE_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAGE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    write_label_master()
    write_query_plan()
    expand_question_map()
    expand_triage_rules()
    print(f"Wrote {LABEL_MASTER_PATH}")
    print(f"Wrote {QUERY_PLAN_PATH}")
    print(f"Expanded {QUESTION_MAP_PATH}")
    print(f"Expanded {TRIAGE_RULE_PATH}")


if __name__ == "__main__":
    main()
