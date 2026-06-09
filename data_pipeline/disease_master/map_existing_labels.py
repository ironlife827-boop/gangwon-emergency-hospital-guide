from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MASTER_PATH = DATA_DIR / "disease_master.csv"

TARGET_FILES = [
    "naver_kin_symptom_cases.csv",
    "disease_question_map.csv",
    "triage_rule_dataset.csv",
    "emergency_disease_label_master.csv",
]

ALIAS_CANONICAL = {
    "AMI": "급성 심근경색",
    "심근경색": "급성 심근경색",
    "급성심근경색": "급성 심근경색",
    "급성 충수염": "맹장염",
    "충수염": "맹장염",
    "급성충수염": "맹장염",
    "개방성골절": "개방성 골절",
    "패혈증": "패혈증 의심",
    "뇌수막염": "수막염 의심",
    "수막염": "수막염 의심",
    "노로바이러스": "노로바이러스 의심 급성 위장염",
    "노로바이러스 장염": "노로바이러스 의심 급성 위장염",
    "감전": "전기손상",
    "아나필락시스 의심": "아나필락시스",
    "뇌진탕": "뇌진탕 의심 두부손상",
    "두부손상": "뇌진탕 의심 두부손상",
    "소아 고열 경련": "열성경련",
    "고열 경련": "열성경련",
    "탈수": "중증 탈수",
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


def build_lookup(master: pd.DataFrame) -> dict[str, dict]:
    lookup: dict[str, dict] = {}

    for _, row in master.iterrows():
        names = [str(row["disease_name"])]
        names.extend(
            alias.strip()
            for alias in str(row.get("aliases", "")).split(";")
            if alias.strip()
        )

        for name in names:
            for key in {normalize_label(name), canonical_name(name), normalize_label(name).replace(" ", "")}:
                if key:
                    lookup[key] = {
                        "disease_id": str(row["disease_id"]),
                        "canonical_disease_name": str(row["disease_name"]),
                    }

    return lookup


def map_disease(value: str, lookup: dict[str, dict]) -> dict:
    label = normalize_label(value)
    keys = [label, canonical_name(label), label.replace(" ", ""), canonical_name(label).replace(" ", "")]

    for key in keys:
        if key in lookup:
            return lookup[key]

    return {"disease_id": "", "canonical_disease_name": label}


def mapped_output_path(path: Path) -> Path:
    return path.with_name(path.stem + "_mapped.csv")


def map_file(path: Path, lookup: dict[str, dict]) -> tuple[Path, int]:
    df = pd.read_csv(path)
    if "suspected_disease" not in df.columns:
        return mapped_output_path(path), 0

    mapped = df["suspected_disease"].map(lambda value: map_disease(str(value), lookup))
    df["disease_id"] = mapped.map(lambda item: item["disease_id"])
    df["canonical_disease_name"] = mapped.map(lambda item: item["canonical_disease_name"])

    output_path = mapped_output_path(path)
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    unmapped_count = int((df["disease_id"].astype(str).str.len() == 0).sum())
    return output_path, unmapped_count


def main() -> None:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing disease master: {MASTER_PATH}")

    master = pd.read_csv(MASTER_PATH)
    lookup = build_lookup(master)

    print("===== mapping existing disease labels =====")
    for filename in TARGET_FILES:
        path = PROCESSED_DIR / filename
        if not path.exists():
            print(f"SKIP missing {filename}")
            continue

        output_path, unmapped_count = map_file(path, lookup)
        print(f"{filename} -> {output_path.name} / unmapped={unmapped_count}")


if __name__ == "__main__":
    main()
