from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "transformer_symptom_classifier"

TARGET_COLUMNS = ["symptom_group", "department", "suspected_disease"]


def predict_one(model_dir: Path, text: str) -> dict:
    with open(model_dir / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(model_dir / "model")
    model = AutoModelForSequenceClassification.from_pretrained(model_dir / "model")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    top_idx = int(torch.argmax(probs).item())
    label = metadata["labels"][top_idx]
    confidence = float(probs[top_idx].item())

    return {
        "label": label,
        "confidence": round(confidence, 4),
    }


def predict(text: str, model_root: Path) -> dict:
    result = {}

    for target in TARGET_COLUMNS:
        target_dir = model_root / target
        if not target_dir.exists():
            result[target] = {
                "label": None,
                "confidence": 0,
                "error": f"Missing model directory: {target_dir}",
            }
            continue

        result[target] = predict_one(target_dir, text)

    return result


def parse_args():
    parser = argparse.ArgumentParser(
        description="Predict symptom labels using local Transformer models."
    )

    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="User symptom text.",
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=DEFAULT_MODEL_DIR,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    result = predict(args.text, args.model_root)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
