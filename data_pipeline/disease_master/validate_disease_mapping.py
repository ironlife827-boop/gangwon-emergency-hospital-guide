from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MASTER_PATH = DATA_DIR / "disease_master.csv"

MAPPED_FILES = [
    "naver_kin_symptom_cases_mapped.csv",
    "disease_question_map_mapped.csv",
    "triage_rule_dataset_mapped.csv",
    "emergency_disease_label_master_mapped.csv",
]


def fail(message: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {message}")


def main() -> None:
    if not MASTER_PATH.exists():
        fail(f"missing {MASTER_PATH}")

    master = pd.read_csv(MASTER_PATH)
    required_master_columns = {
        "disease_id",
        "disease_name",
        "aliases",
        "symptom_group",
        "department",
        "severity_level",
        "required_resource_code",
        "is_emergency",
        "is_model_target",
        "mapping_status",
    }
    missing = required_master_columns - set(master.columns)
    if missing:
        fail(f"disease_master missing columns: {sorted(missing)}")

    if master["disease_id"].isna().any() or (master["disease_id"].astype(str).str.len() == 0).any():
        fail("empty disease_id in disease_master")
    if master["disease_id"].duplicated().any():
        duplicated = master.loc[master["disease_id"].duplicated(), "disease_id"].tolist()
        fail(f"duplicated disease_id: {duplicated[:10]}")
    if master["disease_name"].duplicated().any():
        duplicated = master.loc[master["disease_name"].duplicated(), "disease_name"].tolist()
        fail(f"duplicated disease_name: {duplicated[:10]}")

    master_ids = set(master["disease_id"].astype(str))
    print("===== disease master =====")
    print(f"diseases: {len(master)}")
    print(f"model targets: {int(master['is_model_target'].sum())}")
    print(f"emergency diseases: {int(master['is_emergency'].sum())}")
    print(f"symptom groups: {master['symptom_group'].nunique()}")

    failures: list[str] = []

    for filename in MAPPED_FILES:
        path = PROCESSED_DIR / filename
        if not path.exists():
            failures.append(f"missing mapped file: {filename}")
            continue

        df = pd.read_csv(path)
        for column in ["disease_id", "canonical_disease_name"]:
            if column not in df.columns:
                failures.append(f"{filename} missing {column}")

        empty_ids = int(df["disease_id"].fillna("").astype(str).eq("").sum())
        unknown_ids = sorted(set(df["disease_id"].dropna().astype(str)) - master_ids)

        if empty_ids:
            failures.append(f"{filename} has {empty_ids} unmapped rows")
        if unknown_ids:
            failures.append(f"{filename} has unknown disease_id values: {unknown_ids[:10]}")

        print(
            f"{filename}: rows={len(df)}, diseases={df['disease_id'].nunique()}, "
            f"unmapped={empty_ids}"
        )

    naver_path = PROCESSED_DIR / "naver_kin_symptom_cases_mapped.csv"
    if naver_path.exists():
        naver = pd.read_csv(naver_path)
        counts = naver.groupby("disease_id").size().sort_values(ascending=False)
        print("top mapped training disease counts:")
        for disease_id, count in counts.head(10).items():
            name = master.loc[master["disease_id"].eq(disease_id), "disease_name"].iloc[0]
            print(f"- {disease_id} {name}: {count}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
