from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "naver_kin_symptom_cases.csv"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "symptom_classifier.pkl"


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    required_columns = [
        "cleaned_text",
        "symptom_keywords",
        "symptom_group",
        "department",
        "suspected_disease",
        "severity_level",
    ]

    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    for column in required_columns:
        df[column] = df[column].fillna("").astype(str)

    df["input_text"] = (
        df["cleaned_text"]
        + " "
        + df["symptom_keywords"].str.replace(";", " ", regex=False)
    ).str.strip()

    df = df[df["input_text"].str.len() > 0].copy()

    return df


def train_single_label_model(df: pd.DataFrame, target_column: str) -> Pipeline:
    X = df["input_text"]
    y = df[target_column]

    if target_column == "suspected_disease":
        vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            max_features=10000,
        )
    else:
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            min_df=1,
            max_features=8000,
        )

    model = Pipeline(
        steps=[
            ("tfidf", vectorizer),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # 클래스 수가 너무 작거나 샘플 수가 부족한 경우 stratify 실패 가능성 방지
    stratify = y if y.value_counts().min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\\n===== {target_column} classification report =====")
    print(classification_report(y_test, y_pred, zero_division=0))

    return model


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()

    print(f"Loaded dataset: {len(df)} rows")
    print("Targets:")
    print("- symptom_group:", df["symptom_group"].nunique())
    print("- department:", df["department"].nunique())
    print("- suspected_disease:", df["suspected_disease"].nunique())

    symptom_group_model = train_single_label_model(df, "symptom_group")
    department_model = train_single_label_model(df, "department")
    disease_model = train_single_label_model(df, "suspected_disease")

    payload = {
        "symptom_group_model": symptom_group_model,
        "department_model": department_model,
        "disease_model": disease_model,
        "metadata": {
            "train_rows": len(df),
            "source": "naver_kin_symptom_cases.csv",
            "model_type": "TF-IDF + LogisticRegression; suspected_disease uses word 1-2gram, other targets use char_wb 2-5gram",
        },
    }

    joblib.dump(payload, MODEL_PATH)

    print(f"\\nSaved model: {MODEL_PATH}")


if __name__ == "__main__":
    main()
