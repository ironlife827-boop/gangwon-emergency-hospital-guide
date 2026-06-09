from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MASTER_PATH = DATA_DIR / "disease_master.csv"

SOURCE_FILES = [
    ("naver_kin_symptom_cases.csv", "naver_kin", "suspected_disease"),
    ("disease_question_map.csv", "question_map", "suspected_disease"),
    ("triage_rule_dataset.csv", "triage_rule", "suspected_disease"),
    ("emergency_disease_label_master.csv", "emergency_master", "suspected_disease"),
]

MASTER_COLUMNS = [
    "disease_id",
    "disease_name",
    "aliases",
    "symptom_group",
    "body_part",
    "disease_category",
    "symptoms",
    "related_diseases",
    "department",
    "severity_level",
    "required_resource_code",
    "is_emergency",
    "is_model_target",
    "source",
    "mapping_status",
]

GROUP_CODE = {
    "abdominal": "DIG",
    "allergy": "ALG",
    "bleeding": "BLD",
    "cardio": "CAR",
    "endocrine": "END",
    "ent": "ENT",
    "eye": "EYE",
    "foreign_body": "FB",
    "hematology": "HEM",
    "infection": "INF",
    "musculoskeletal": "MSK",
    "neuro": "NEU",
    "obgy": "OBG",
    "pediatric": "PED",
    "psychiatric": "PSY",
    "respiratory": "RESP",
    "skin": "SKIN",
    "surgery": "SURG",
    "toxic": "TOX",
    "trauma": "TRM",
    "urology": "URO",
}

BODY_PART_BY_GROUP = {
    "abdominal": "abdomen",
    "allergy": "systemic",
    "bleeding": "systemic",
    "cardio": "heart",
    "endocrine": "endocrine",
    "ent": "ear_nose_throat",
    "eye": "eye",
    "foreign_body": "airway_or_body",
    "hematology": "blood",
    "infection": "systemic",
    "musculoskeletal": "musculoskeletal",
    "neuro": "brain_nerve",
    "obgy": "obgy",
    "pediatric": "pediatric",
    "psychiatric": "mental_health",
    "respiratory": "lung_airway",
    "skin": "skin",
    "surgery": "surgery",
    "toxic": "toxic_exposure",
    "trauma": "trauma",
    "urology": "urinary",
}

RESOURCE_BY_GROUP = {
    "cardio": "ER_CARDIO",
    "neuro": "ER_NEURO",
    "respiratory": "ER_RESP",
    "trauma": "ER_TRAUMA",
    "bleeding": "ER_TRAUMA",
    "pediatric": "ER_PED",
    "surgery": "ER_GENERAL",
}

ALIAS_CANONICAL = {
    "AMI": "급성 심근경색",
    "심근경색": "급성 심근경색",
    "급성심근경색": "급성 심근경색",
    "부정맥": "부정맥",
    "급성 충수염": "맹장염",
    "충수염": "맹장염",
    "급성충수염": "맹장염",
    "개방성골절": "개방성 골절",
    "개방성 골절": "개방성 골절",
    "패혈증": "패혈증 의심",
    "패혈증 의심": "패혈증 의심",
    "뇌수막염": "수막염 의심",
    "수막염": "수막염 의심",
    "수막염 의심": "수막염 의심",
    "노로바이러스": "노로바이러스 의심 급성 위장염",
    "노로바이러스 장염": "노로바이러스 의심 급성 위장염",
    "전기손상": "전기손상",
    "감전": "전기손상",
    "아나필락시스 의심": "아나필락시스",
    "뇌진탕": "뇌진탕 의심 두부손상",
    "두부손상": "뇌진탕 의심 두부손상",
    "소아 고열 경련": "열성경련",
    "고열 경련": "열성경련",
    "탈수": "중증 탈수",
}

EXTRA_ALIASES = {
    "열성경련": ["소아 고열 경련", "고열 경련"],
    "중증 탈수": ["탈수"],
    "급성 심근경색": ["심근경색", "AMI"],
    "맹장염": ["급성 충수염", "충수염"],
    "패혈증 의심": ["패혈증"],
    "수막염 의심": ["뇌수막염", "수막염"],
    "전기손상": ["감전"],
    "뇌진탕 의심 두부손상": ["뇌진탕", "두부손상"],
}


def normalize_label(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("(의심)", " 의심")
    return text.strip()


def canonical_name(value: str) -> str:
    label = normalize_label(value)
    compact = label.replace(" ", "")
    if label in ALIAS_CANONICAL:
        return ALIAS_CANONICAL[label]
    if compact in ALIAS_CANONICAL:
        return ALIAS_CANONICAL[compact]
    return label


def majority(values: list[str], fallback: str = "") -> str:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    if not cleaned:
        return fallback
    return Counter(cleaned).most_common(1)[0][0]


def split_keywords(value: str) -> list[str]:
    chunks = re.split(r"[;,/|]", str(value or ""))
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def collect_sources() -> dict[str, dict]:
    records: dict[str, dict] = defaultdict(
        lambda: {
            "aliases": set(),
            "groups": [],
            "departments": [],
            "severity_levels": [],
            "keywords": [],
            "sources": set(),
            "is_model_target": False,
            "is_emergency": False,
        }
    )

    for filename, source_name, disease_column in SOURCE_FILES:
        path = PROCESSED_DIR / filename
        if not path.exists():
            continue

        df = pd.read_csv(path)
        if disease_column not in df.columns:
            continue

        for _, row in df.iterrows():
            raw_disease = normalize_label(row.get(disease_column, ""))
            if not raw_disease:
                continue

            name = canonical_name(raw_disease)
            item = records[name]
            item["aliases"].add(raw_disease)
            item["sources"].add(source_name)

            if "symptom_group" in row and str(row.get("symptom_group", "")).strip():
                item["groups"].append(str(row["symptom_group"]).strip())
            if "department" in row and str(row.get("department", "")).strip():
                item["departments"].append(str(row["department"]).strip())
            if "severity_level" in row:
                try:
                    item["severity_levels"].append(int(float(row["severity_level"])))
                except (TypeError, ValueError):
                    pass
            if "symptom_keywords" in row:
                item["keywords"].extend(split_keywords(str(row.get("symptom_keywords", ""))))
            if "search_keywords" in row:
                item["keywords"].extend(split_keywords(str(row.get("search_keywords", ""))))
            if source_name == "naver_kin":
                item["is_model_target"] = True
            if source_name in {"emergency_master", "triage_rule"}:
                item["is_emergency"] = True

    return records


def disease_category(symptom_group: str, is_emergency: bool) -> str:
    if is_emergency:
        return "emergency"
    if symptom_group in {"respiratory", "abdominal", "ent", "skin", "psychiatric"}:
        return "primary_care"
    return "specialty_care"


def make_disease_id(symptom_group: str, sequence: int) -> str:
    code = GROUP_CODE.get(symptom_group, "ETC")
    return f"D_{code}_{sequence:03d}"


def build_master() -> pd.DataFrame:
    records = collect_sources()
    rows = []
    sequence_by_group: Counter[str] = Counter()

    for disease_name in sorted(records):
        item = records[disease_name]
        symptom_group = majority(item["groups"], "etc")
        sequence_by_group[symptom_group] += 1
        severity = max(item["severity_levels"]) if item["severity_levels"] else 1
        is_emergency = bool(item["is_emergency"] or severity >= 4)
        source_names = sorted(item["sources"])
        aliases = set(alias for alias in item["aliases"] if alias != disease_name)
        aliases.update(EXTRA_ALIASES.get(disease_name, []))
        aliases = sorted(alias for alias in aliases if alias != disease_name)
        symptoms = sorted(set(item["keywords"]))[:30]

        rows.append(
            {
                "disease_id": make_disease_id(symptom_group, sequence_by_group[symptom_group]),
                "disease_name": disease_name,
                "aliases": ";".join(aliases),
                "symptom_group": symptom_group,
                "body_part": BODY_PART_BY_GROUP.get(symptom_group, ""),
                "disease_category": disease_category(symptom_group, is_emergency),
                "symptoms": ";".join(symptoms),
                "related_diseases": "",
                "department": majority(item["departments"], "내과"),
                "severity_level": max(1, min(5, int(severity))),
                "required_resource_code": RESOURCE_BY_GROUP.get(symptom_group, "ER_GENERAL" if is_emergency else "OPD_GENERAL"),
                "is_emergency": int(is_emergency),
                "is_model_target": int(bool(item["is_model_target"])),
                "source": ";".join(source_names),
                "mapping_status": "mapped",
            }
        )

    return pd.DataFrame(rows, columns=MASTER_COLUMNS)


def main() -> None:
    master = build_master()
    MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(
        MASTER_PATH,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    print("===== disease_master built =====")
    print(f"output: {MASTER_PATH}")
    print(f"diseases: {len(master)}")
    print(f"model targets: {int(master['is_model_target'].sum())}")
    print(f"emergency diseases: {int(master['is_emergency'].sum())}")
    print(f"symptom groups: {master['symptom_group'].nunique()}")


if __name__ == "__main__":
    main()
