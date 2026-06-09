# Model Design V2

## Model Role

The model is used to produce symptom and suspected disease candidates. It is not the final medical authority. Red flags, follow-up answers, and resource rules remain separate from disease prediction.

## Current Artifact

`models/symptom_classifier.pkl`

Payload keys:

- `symptom_group_model`
- `department_model`
- `disease_model`
- `disease_id_model`
- `metadata`

The previous disease-name model is still present for compatibility. The new `disease_id_model` predicts the stable key from `data/disease_master.csv`.

## Training Data

Primary training source:

- `data/processed/naver_kin_symptom_cases_mapped.csv`

Fallback source:

- `data/processed/naver_kin_symptom_cases.csv`

The mapped file preserves the original columns and adds:

- `disease_id`
- `canonical_disease_name`

## Prediction Output

The backend keeps the existing display fields:

- `suspected_disease`
- `symptom_group`
- `department`

It also returns candidate metadata:

```json
[
  {
    "disease_id": "D_RESP_001",
    "disease_name": "감기",
    "confidence": 0.42
  }
]
```

The displayed disease name should be understood as a suspected candidate, not a diagnosis.

## Severity

Severity is not a standalone ML model. It is calculated from:

- red-flag rules
- selected follow-up questions
- `risk_score` from `disease_question_map_mapped.csv`
- fallback `triage_rule_dataset_mapped.csv`

The final risk score is clamped to 10 and converted to the 1-5 severity scale.

## Validation

The current smoke test covers:

- emergency examples such as electric injury, stroke, anaphylaxis, severe chest pain
- common symptoms such as cold, flu, COVID-19, gastroenteritis, appendicitis
- regular hospital routing for non-emergency cold symptoms

Run:

```powershell
python -X utf8 data_pipeline\symptom_model\smoke_test_triage_quality.py
```
