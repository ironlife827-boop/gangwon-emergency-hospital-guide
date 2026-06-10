from __future__ import annotations

import argparse
import json
from pathlib import Path

import evaluate
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "naver_kin_symptom_cases.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "models" / "transformer_symptom_classifier"

TARGET_COLUMNS = ["symptom_group", "department", "suspected_disease"]


def load_dataset(data_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_path)

    required = [
        "cleaned_text",
        "symptom_keywords",
        "symptom_group",
        "department",
        "suspected_disease",
    ]

    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    for column in required:
        df[column] = df[column].fillna("").astype(str)

    df["input_text"] = (
        df["cleaned_text"]
        + " "
        + df["symptom_keywords"].str.replace(";", " ", regex=False)
    ).str.strip()

    df = df[df["input_text"].str.len() > 0].copy()
    df = df.reset_index(drop=True)

    return df


def compute_metrics_builder():
    accuracy_metric = evaluate.load("accuracy")
    f1_metric = evaluate.load("f1")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)

        accuracy = accuracy_metric.compute(predictions=predictions, references=labels)["accuracy"]
        macro_f1 = f1_metric.compute(
            predictions=predictions,
            references=labels,
            average="macro",
        )["f1"]
        weighted_f1 = f1_metric.compute(
            predictions=predictions,
            references=labels,
            average="weighted",
        )["f1"]

        return {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
        }

    return compute_metrics


def train_one_target(
    df: pd.DataFrame,
    target_column: str,
    model_name: str,
    output_dir: Path,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    max_length: int,
):
    print(f"\n==============================")
    print(f"Training target: {target_column}")
    print(f"Model: {model_name}")
    print(f"Rows: {len(df)}")
    print(f"Classes: {df[target_column].nunique()}")
    print(f"==============================\n")

    target_dir = output_dir / target_column
    target_dir.mkdir(parents=True, exist_ok=True)

    label_encoder = LabelEncoder()
    df = df.copy()
    df["label"] = label_encoder.fit_transform(df[target_column])

    # 클래스별 샘플 수가 2개 미만이면 stratify가 깨질 수 있으므로 방어.
    stratify = df["label"] if df["label"].value_counts().min() >= 2 else None

    train_df, valid_df = train_test_split(
        df[["input_text", "label", target_column]],
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(batch):
        return tokenizer(
            batch["input_text"],
            truncation=True,
            max_length=max_length,
        )

    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    valid_dataset = Dataset.from_pandas(valid_df.reset_index(drop=True))

    train_dataset = train_dataset.map(tokenize, batched=True)
    valid_dataset = valid_dataset.map(tokenize, batched=True)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(label_encoder.classes_),
        id2label={idx: label for idx, label in enumerate(label_encoder.classes_)},
        label2id={label: idx for idx, label in enumerate(label_encoder.classes_)},
    )

    training_args = TrainingArguments(
        output_dir=str(target_dir / "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=20,
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="weighted_f1",
        greater_is_better=True,
        save_total_limit=1,
        report_to="none",
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics_builder(),
    )

    trainer.train()

    eval_metrics = trainer.evaluate()
    print(f"\nEval metrics for {target_column}:")
    print(eval_metrics)

    predictions = trainer.predict(valid_dataset)
    y_pred = np.argmax(predictions.predictions, axis=-1)
    y_true = predictions.label_ids

    report = classification_report(
        y_true,
        y_pred,
        target_names=label_encoder.classes_,
        zero_division=0,
        output_dict=True,
    )

    print("\nClassification report:")
    print(classification_report(
        y_true,
        y_pred,
        target_names=label_encoder.classes_,
        zero_division=0,
    ))

    trainer.save_model(str(target_dir / "model"))
    tokenizer.save_pretrained(str(target_dir / "model"))

    metadata = {
        "target_column": target_column,
        "model_name": model_name,
        "num_labels": len(label_encoder.classes_),
        "labels": label_encoder.classes_.tolist(),
        "eval_metrics": eval_metrics,
        "classification_report": report,
    }

    with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return eval_metrics


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train local Korean Transformer models for symptom classification."
    )

    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"Dataset path. Default: {DEFAULT_DATA_PATH}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output model directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="monologg/koelectra-base-v3-discriminator",
        help="Hugging Face model name.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=128,
    )
    parser.add_argument(
        "--target",
        type=str,
        default="all",
        choices=["all", "symptom_group", "department", "suspected_disease"],
        help="Target column to train.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    df = load_dataset(args.data)
    args.output.mkdir(parents=True, exist_ok=True)

    targets = TARGET_COLUMNS if args.target == "all" else [args.target]

    summary = {
        "data_path": str(args.data),
        "rows": len(df),
        "model_name": args.model_name,
        "targets": {},
    }

    for target_column in targets:
        metrics = train_one_target(
            df=df,
            target_column=target_column,
            model_name=args.model_name,
            output_dir=args.output,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
        )
        summary["targets"][target_column] = metrics

    with open(args.output / "training_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n==============================")
    print("Transformer training complete.")
    print(f"Saved to: {args.output}")
    print("==============================")


if __name__ == "__main__":
    main()
