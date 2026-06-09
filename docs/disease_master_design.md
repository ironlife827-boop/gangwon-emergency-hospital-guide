# Disease Master Design

## Purpose

This project is an emergency/regular hospital guidance system, not a definitive diagnostic system. Disease names are used as suspected disease candidates that connect symptom classification, follow-up questions, severity scoring, resource requirements, and hospital recommendation.

The previous data files used free-text disease labels independently. For example, the same clinical concept could appear as `급성 심근경색`, `심근경색`, or `AMI`. The disease master adds a stable `disease_id` so existing data can stay intact while the system uses one internal key.

## Active Master File

`data/disease_master.csv`

Columns:

- `disease_id`: stable internal key
- `disease_name`: canonical display name
- `aliases`: semicolon-separated alternative names
- `symptom_group`: normalized symptom group
- `body_part`: broad body part/category
- `disease_category`: emergency, primary care, or specialty care
- `symptoms`: compact symptom keywords from existing data
- `related_diseases`: reserved for future candidate grouping
- `department`: representative department
- `severity_level`: source severity hint, 1-5
- `required_resource_code`: resource requirement hint
- `is_emergency`: whether emergency resources may be needed
- `is_model_target`: whether the disease appears in Naver symptom training data
- `source`: source files that contributed the disease
- `mapping_status`: mapping status

## Generated Mapped Files

Original CSV files are preserved. The mapped files add `disease_id` and `canonical_disease_name`.

- `data/processed/naver_kin_symptom_cases_mapped.csv`
- `data/processed/disease_question_map_mapped.csv`
- `data/processed/triage_rule_dataset_mapped.csv`
- `data/processed/emergency_disease_label_master_mapped.csv`

## Pipeline

Run in this order:

```powershell
python -X utf8 data_pipeline\disease_master\build_disease_master.py
python -X utf8 data_pipeline\disease_master\map_existing_labels.py
python -X utf8 data_pipeline\disease_master\validate_disease_mapping.py
```

Current validation summary:

- Disease master rows: 149
- Naver training rows mapped: 3,499
- Naver training disease IDs: 118
- Question map disease IDs: 121
- Triage rule disease IDs: 101
- Emergency master disease IDs: 54
- Unmapped rows: 0

## Design Rule

The frontend may still show a readable suspected disease name. Backend logic should prefer `disease_id` for matching questions, cases, resource rules, and future candidate ranking.
