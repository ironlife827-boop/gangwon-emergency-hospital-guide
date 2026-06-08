from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "naver_kin_symptom_cases_1500_balanced.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "naver_kin_symptom_cases.csv"
DEFAULT_REMOVED_LOG = PROJECT_ROOT / "data" / "processed" / "naver_kin_removed_rows.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "data" / "processed" / "naver_kin_label_summary.csv"


REQUIRED_COLUMNS = [
    "case_id",
    "raw_text",
    "cleaned_text",
    "symptom_keywords",
    "symptom_group",
    "department",
    "suspected_disease",
    "severity_level",
]


# 명백한 라벨 오류 보정 규칙.
# 필요하면 계속 추가하면 된다.
DISEASE_FIX_RULES = {
    "탈구": {
        "symptom_group": "trauma",
        "department": "정형외과",
    },
    "골절": {
        "symptom_group": "trauma",
        "department": "정형외과",
    },
    "화상": {
        "symptom_group": "trauma",
        "department": "응급의학과",
    },
    "전기손상": {
        "symptom_group": "trauma",
        "department": "응급의학과",
    },
    "익수": {
        "symptom_group": "respiratory",
        "department": "응급의학과",
    },
    "질식": {
        "symptom_group": "respiratory",
        "department": "응급의학과",
    },
    "기도폐쇄": {
        "symptom_group": "respiratory",
        "department": "응급의학과",
    },
    "호흡부전": {
        "symptom_group": "respiratory",
        "department": "호흡기내과",
    },
    "약물중독": {
        "symptom_group": "toxic",
        "department": "응급의학과",
    },
    "화학물질 중독": {
        "symptom_group": "toxic",
        "department": "응급의학과",
    },
    "일산화탄소중독": {
        "symptom_group": "toxic",
        "department": "응급의학과",
    },
    "벌쏘임": {
        "symptom_group": "allergy",
        "department": "응급의학과",
    },
    "독사교상": {
        "symptom_group": "toxic",
        "department": "응급의학과",
    },
    "아나필락시스": {
        "symptom_group": "allergy",
        "department": "알레르기내과",
    },
    "대량출혈": {
        "symptom_group": "bleeding",
        "department": "응급의학과",
    },
    "심정지": {
        "symptom_group": "cardio",
        "department": "응급의학과",
    },
    "급성 심근경색": {
        "symptom_group": "cardio",
        "department": "심장내과",
    },
    "부정맥": {
        "symptom_group": "cardio",
        "department": "심장내과",
    },
    "뇌졸중": {
        "symptom_group": "neuro",
        "department": "신경과",
    },
    "외상성 뇌손상": {
        "symptom_group": "neuro",
        "department": "응급의학과",
    },
    "급성 시력상실": {
        "symptom_group": "eye",
        "department": "안과",
    },
    "눈 이물": {
        "symptom_group": "eye",
        "department": "안과",
    },
    "귀 이물": {
        "symptom_group": "foreign_body",
        "department": "이비인후과",
    },
    "코 이물": {
        "symptom_group": "foreign_body",
        "department": "이비인후과",
    },
    "항문 이물": {
        "symptom_group": "foreign_body",
        "department": "외과",
    },
    "위장관출혈": {
        "symptom_group": "abdominal",
        "department": "소화기내과",
    },
    "장폐색": {
        "symptom_group": "abdominal",
        "department": "소화기내과",
    },
    "급성복증": {
        "symptom_group": "abdominal",
        "department": "소화기내과",
    },
    "신부전": {
        "symptom_group": "urology",
        "department": "비뇨의학과",
    },
    "배뇨장애": {
        "symptom_group": "urology",
        "department": "비뇨의학과",
    },
    "산과적 응급상황": {
        "symptom_group": "obgy",
        "department": "산부인과",
    },
    "정신과적 응급상황": {
        "symptom_group": "psychiatric",
        "department": "정신건강의학과",
    },
}


# 너무 기계적으로 생성된 문장 또는 품질 낮은 문장을 제거하기 위한 패턴.
# 과도하게 지우지 않도록 보수적으로 운영한다.
BAD_TEXT_PATTERNS = [
    "가 계속됩니다",
    "증상인데 위험한가요",
    "때문에 병원 가야 하나요",
    "어떻게 해야 하나요",
    "관련 문의",
    "질문드립니다",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")


def fill_missing_keywords(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    missing_mask = df["symptom_keywords"].str.strip().eq("")
    df.loc[missing_mask, "symptom_keywords"] = (
        df.loc[missing_mask, "cleaned_text"]
        .str.replace(",", " ", regex=False)
        .str.replace("/", " ", regex=False)
        .str.replace("  ", " ", regex=False)
    )

    return df


def apply_label_fix_rules(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for disease, fix in DISEASE_FIX_RULES.items():
        mask = df["suspected_disease"].eq(disease)

        for column, value in fix.items():
            df.loc[mask, column] = value

    # unknown은 그대로 두지 않는다.
    unknown_mask = df["symptom_group"].eq("unknown")
    df.loc[unknown_mask & df["suspected_disease"].eq("탈구"), "symptom_group"] = "trauma"
    df.loc[unknown_mask & df["suspected_disease"].eq("탈구"), "department"] = "정형외과"

    # 그래도 unknown이 남으면 etc_emerg로 보낸다.
    df.loc[df["symptom_group"].eq("unknown"), "symptom_group"] = "etc_emerg"

    return df


def remove_bad_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    df["remove_reason"] = ""

    # cleaned_text가 너무 짧은 행 제거
    short_mask = df["cleaned_text"].str.len() < 4
    df.loc[short_mask, "remove_reason"] = "too_short"

    # 저품질 패턴 제거
    for pattern in BAD_TEXT_PATTERNS:
        mask = df["cleaned_text"].str.contains(pattern, na=False)
        df.loc[mask & df["remove_reason"].eq(""), "remove_reason"] = f"bad_pattern:{pattern}"

    # 필수 라벨 누락 제거
    for column in ["cleaned_text", "symptom_group", "department", "suspected_disease"]:
        mask = df[column].str.strip().eq("")
        df.loc[mask & df["remove_reason"].eq(""), "remove_reason"] = f"missing:{column}"

    removed = df[~df["remove_reason"].eq("")].copy()
    cleaned = df[df["remove_reason"].eq("")].drop(columns=["remove_reason"]).copy()

    return cleaned, removed


def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()

    duplicated_mask = df.duplicated(
        subset=["cleaned_text", "suspected_disease"],
        keep="first",
    )

    removed = df[duplicated_mask].copy()
    if not removed.empty:
        removed["remove_reason"] = "duplicate:cleaned_text+suspected_disease"

    cleaned = df[~duplicated_mask].copy()

    return cleaned, removed


def normalize_severity(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["severity_level"] = pd.to_numeric(df["severity_level"], errors="coerce")
    df["severity_level"] = df["severity_level"].fillna(3).astype(int)
    df["severity_level"] = df["severity_level"].clip(1, 5)

    return df


def rebuild_case_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.reset_index(drop=True)
    df["case_id"] = range(1, len(df) + 1)
    return df


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["symptom_group", "department", "suspected_disease"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "symptom_group", "suspected_disease"], ascending=[False, True, True])
    )

    return summary


def clean_dataset(input_path: Path, output_path: Path, removed_log_path: Path, summary_path: Path) -> None:
    df = pd.read_csv(input_path)
    validate_columns(df)

    original_count = len(df)

    for column in REQUIRED_COLUMNS:
        df[column] = df[column].apply(normalize_text)

    df = normalize_severity(df)
    df = fill_missing_keywords(df)
    df = apply_label_fix_rules(df)

    df, removed_bad = remove_bad_rows(df)
    df, removed_dup = remove_duplicates(df)

    removed_all = pd.concat([removed_bad, removed_dup], ignore_index=True)
    df = rebuild_case_id(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    removed_log_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    removed_all.to_csv(removed_log_path, index=False, encoding="utf-8-sig")
    build_summary(df).to_csv(summary_path, index=False, encoding="utf-8-sig")

    print("===== Naver KIN symptom dataset cleaning complete =====")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Original rows: {original_count}")
    print(f"Cleaned rows: {len(df)}")
    print(f"Removed rows: {len(removed_all)}")
    print()
    print("===== Symptom group counts =====")
    print(df["symptom_group"].value_counts())
    print()
    print("===== Department counts =====")
    print(df["department"].value_counts())
    print()
    print("===== Suspected disease counts, bottom 20 =====")
    print(df["suspected_disease"].value_counts().tail(20))
    print()
    print(f"Removed row log: {removed_log_path}")
    print(f"Label summary: {summary_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean and normalize naver_kin_symptom_cases dataset."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input CSV path. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--removed-log",
        type=Path,
        default=DEFAULT_REMOVED_LOG,
        help=f"Removed rows log path. Default: {DEFAULT_REMOVED_LOG}",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
        help=f"Label summary output path. Default: {DEFAULT_SUMMARY}",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    clean_dataset(
        input_path=args.input,
        output_path=args.output,
        removed_log_path=args.removed_log,
        summary_path=args.summary,
    )
