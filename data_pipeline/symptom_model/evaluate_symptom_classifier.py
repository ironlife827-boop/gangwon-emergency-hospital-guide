from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "naver_kin_symptom_cases.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "model_evaluation"
DOCS_DIR = PROJECT_ROOT / "docs"

TARGET_COLUMNS = ["symptom_group", "department", "suspected_disease"]
RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    required_columns = [
        "case_id",
        "raw_text",
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


def build_models() -> dict[str, Pipeline]:
    return {
        "baseline_most_frequent": Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 1))),
                ("clf", DummyClassifier(strategy="most_frequent")),
            ]
        ),
        "word_tfidf_logreg": Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="word",
                        ngram_range=(1, 2),
                        min_df=1,
                        max_features=10000,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "char_tfidf_logreg": Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(2, 5),
                        min_df=1,
                        max_features=8000,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "char_tfidf_linear_svc": Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(2, 5),
                        min_df=1,
                        max_features=12000,
                    ),
                ),
                (
                    "clf",
                    LinearSVC(
                        class_weight="balanced",
                        dual="auto",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def evaluate_target(df: pd.DataFrame, target_column: str) -> tuple[list[dict], dict]:
    x = df["input_text"]
    y = df[target_column]
    stratify = y if y.value_counts().min() >= 2 else None

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )

    rows: list[dict] = []
    best = {"macro_f1": -1.0}

    for model_name, model in build_models().items():
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)

        row = {
            "target": target_column,
            "model": model_name,
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "macro_f1": round(f1_score(y_test, y_pred, average="macro", zero_division=0), 4),
            "weighted_f1": round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4),
            "train_rows": len(x_train),
            "test_rows": len(x_test),
            "classes": y.nunique(),
        }
        rows.append(row)

        if row["macro_f1"] > best["macro_f1"]:
            labels = sorted(y_test.unique().tolist())
            report = classification_report(
                y_test,
                y_pred,
                labels=labels,
                zero_division=0,
                output_dict=True,
            )
            matrix = confusion_matrix(y_test, y_pred, labels=labels)
            best = {
                **row,
                "labels": labels,
                "classification_report": report,
                "confusion_matrix": matrix.tolist(),
            }

    return rows, best


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def build_report(df: pd.DataFrame, summary_rows: list[dict], best_by_target: dict[str, dict]) -> str:
    disease_counts = Counter(df["suspected_disease"])
    group_counts = Counter(df["symptom_group"])
    department_counts = Counter(df["department"])

    summary_table = [["Target", "Model", "Accuracy", "Macro F1", "Weighted F1", "Classes"]]
    for row in summary_rows:
        summary_table.append(
            [
                row["target"],
                row["model"],
                f"{row['accuracy']:.4f}",
                f"{row['macro_f1']:.4f}",
                f"{row['weighted_f1']:.4f}",
                str(row["classes"]),
            ]
        )

    best_table = [["Target", "Best Model", "Accuracy", "Macro F1", "Weighted F1"]]
    for target in TARGET_COLUMNS:
        row = best_by_target[target]
        best_table.append(
            [
                target,
                row["model"],
                f"{row['accuracy']:.4f}",
                f"{row['macro_f1']:.4f}",
                f"{row['weighted_f1']:.4f}",
            ]
        )

    group_table = [["Symptom Group", "Rows"]]
    group_table.extend([[key, str(value)] for key, value in group_counts.most_common()])

    department_table = [["Department", "Rows"]]
    department_table.extend([[key, str(value)] for key, value in department_counts.most_common()])

    disease_table = [["Suspected Disease", "Rows"]]
    disease_table.extend([[key, str(value)] for key, value in disease_counts.most_common()])

    return f"""# Symptom Classifier Evaluation

## Purpose

This report documents the model-centered link in the service: natural-language symptom text is mapped to `symptom_group`, `department`, and `suspected_disease` before triage questions and hospital recommendations are generated.

The emergency triage rule data is not used as the disease classifier. It is used later as a risk-score aid.

## Dataset

- Source: `data/processed/naver_kin_symptom_cases.csv`
- Rows used: {len(df)}
- Input features: `cleaned_text` + `symptom_keywords`
- Targets:
  - `symptom_group`: {df["symptom_group"].nunique()} classes
  - `department`: {df["department"].nunique()} classes
  - `suspected_disease`: {df["suspected_disease"].nunique()} classes
- Train/test split: {int((1 - TEST_SIZE) * 100)}% / {int(TEST_SIZE * 100)}%, stratified by each target

## Model Comparison

Compared models:

- `baseline_most_frequent`: majority-class baseline
- `word_tfidf_logreg`: word unigram/bigram TF-IDF + Logistic Regression
- `char_tfidf_logreg`: character n-gram TF-IDF + Logistic Regression
- `char_tfidf_linear_svc`: character n-gram TF-IDF + Linear SVC

{markdown_table(summary_table)}

## Best Model By Target

{markdown_table(best_table)}

## Data Understanding

### Symptom Group Distribution

{markdown_table(group_table)}

### Department Distribution

{markdown_table(department_table)}

### Suspected Disease Distribution

{markdown_table(disease_table)}

## System Interpretation

The production service prioritizes `symptom_classifier.pkl` for disease and department prediction. After prediction, `disease_question_map.csv` selects disease-specific follow-up questions. Final analysis merges the initial symptom with follow-up answers and runs the classifier again before calculating emergency risk and recommending hospitals.

## Limitations And Next Improvements

- The current dataset is intentionally balanced by suspected disease in the latest processed CSV, which helps model training but may differ from real-world symptom frequency.
- Evaluation uses a held-out split from the same source distribution. A future improvement is to collect a separate human-labeled validation set.
- Transformer fine-tuning is documented separately as a future path, but the current deployed system uses lightweight TF-IDF models for stability and fast inference.
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    summary_rows: list[dict] = []
    best_by_target: dict[str, dict] = {}

    for target in TARGET_COLUMNS:
        rows, best = evaluate_target(df, target)
        summary_rows.extend(rows)
        best_by_target[target] = best

        report_rows = []
        for label, metrics in best["classification_report"].items():
            if not isinstance(metrics, dict):
                continue
            report_rows.append(
                {
                    "label": label,
                    "precision": round(metrics.get("precision", 0), 4),
                    "recall": round(metrics.get("recall", 0), 4),
                    "f1_score": round(metrics.get("f1-score", 0), 4),
                    "support": int(metrics.get("support", 0)),
                }
            )
        write_csv(OUTPUT_DIR / f"{target}_best_model_classification_report.csv", report_rows)

    write_csv(OUTPUT_DIR / "model_comparison_summary.csv", summary_rows)
    report = build_report(df, summary_rows, best_by_target)
    (DOCS_DIR / "symptom_classifier_evaluation.md").write_text(report, encoding="utf-8")

    print(f"Saved summary: {OUTPUT_DIR / 'model_comparison_summary.csv'}")
    print(f"Saved report: {DOCS_DIR / 'symptom_classifier_evaluation.md'}")


if __name__ == "__main__":
    main()
