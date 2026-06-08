from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"


@lru_cache(maxsize=1)
def load_hospitals() -> pd.DataFrame:
    path = DATA_DIR / "hospital_master.csv"
    df = pd.read_csv(path)
    df["department"] = df["department"].fillna("")
    df["hospital_name"] = df["hospital_name"].fillna("")
    df["address"] = df["address"].fillna("")
    df["phone"] = df["phone"].fillna("")
    df["is_emergency"] = df["is_emergency"].fillna(0).astype(int)
    return df


@lru_cache(maxsize=1)
def load_triage_rules() -> pd.DataFrame:
    path = DATA_DIR / "triage_rule_dataset.csv"
    df = pd.read_csv(path)
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0)
    df["answer_option"] = df["answer_option"].fillna("예")
    return df


@lru_cache(maxsize=1)
def load_disease_questions() -> pd.DataFrame:
    path = DATA_DIR / "disease_question_map.csv"
    if not path.exists():
        return pd.DataFrame(columns=["question_id","suspected_disease","symptom_group","question","positive_keywords","risk_score","required_resource_code","importance"])
    df = pd.read_csv(path)
    df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0)
    df["importance"] = pd.to_numeric(df["importance"], errors="coerce").fillna(0)
    for col in ["question_id","suspected_disease","symptom_group","question","positive_keywords","required_resource_code"]:
        df[col] = df[col].fillna("").astype(str)
    return df


@lru_cache(maxsize=1)
def load_naver_cases() -> pd.DataFrame:
    path = DATA_DIR / "naver_kin_symptom_cases.csv"
    df = pd.read_csv(path)
    for col in ["raw_text","cleaned_text","symptom_keywords","symptom_group","department","suspected_disease"]:
        df[col] = df[col].fillna("")
    if "source_url" not in df.columns:
        df["source_url"] = ""
    df["source_url"] = df["source_url"].fillna("")
    df["severity_level"] = pd.to_numeric(df["severity_level"], errors="coerce").fillna(1).astype(int)
    df["search_text"] = (
        df["cleaned_text"].astype(str) + " " +
        df["symptom_keywords"].astype(str).str.replace(";", " ", regex=False) + " " +
        df["symptom_group"].astype(str) + " " +
        df["department"].astype(str) + " " +
        df["suspected_disease"].astype(str)
    )
    return df


@lru_cache(maxsize=1)
def load_beds() -> pd.DataFrame:
    path = DATA_DIR / "gangwon_hospital_with_beds.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["hospital_name"] = df["hospital_name"].fillna("")
    df["hvec"] = pd.to_numeric(df.get("hvec", 0), errors="coerce").fillna(0).astype(int)
    return df


@lru_cache(maxsize=1)
def load_severity_model():
    path = MODEL_DIR / "severity_model.pkl"
    if not path.exists():
        return None
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_eta_model():
    path = MODEL_DIR / "eta_model.pkl"
    if not path.exists():
        return None
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_symptom_classifier():
    path = MODEL_DIR / "symptom_classifier.pkl"
    if not path.exists():
        return None
    return joblib.load(path)
