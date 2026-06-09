# System Architecture V2

## Goal

The service guides users to an appropriate emergency or regular hospital in Gangwon-do. It does not claim to diagnose disease. Suspected disease names are used as candidates for triage, follow-up questions, severity scoring, and hospital routing.

## Flow

1. User enters natural-language symptoms.
2. Red-flag keyword rules protect immediately dangerous cases.
3. `symptom_classifier.pkl` predicts symptom group, department, suspected disease, and disease ID.
4. Disease evidence rules can rerank low-confidence or clinically obvious cases.
5. Disease-specific follow-up questions are selected from `disease_question_map_mapped.csv`.
6. The initial symptom and positive/uncertain answers are merged.
7. Final symptom text is re-analyzed.
8. Severity is calculated by question/rule risk score, clamped to 10.
9. Hospital recommendation uses department, severity, emergency/regular care mode, distance, ETA, and available beds.

## Active Runtime Files

- `models/symptom_classifier.pkl`
- `data/disease_master.csv`
- `data/processed/naver_kin_symptom_cases_mapped.csv`
- `data/processed/disease_question_map_mapped.csv`
- `data/processed/triage_rule_dataset_mapped.csv`
- `data/processed/hospital_master.csv`
- `data/processed/gangwon_hospital_with_beds.csv`

Each mapped file has an original non-mapped CSV fallback. If mapped files are missing, the backend can still run with the previous structure.

## Backend Compatibility

The API still returns existing fields such as:

- `symptom_group`
- `department`
- `suspected_disease`
- `severity_level`
- `hospitals`

It now also exposes:

- `disease_id`
- `canonical_disease_name`
- `disease_candidates`

These additional fields allow future UI improvements without breaking the existing frontend.

## Recommendation Principle

- Severity 1-2: emergency hospital priority, available beds strongly matter.
- Severity 3-5: regular nearby hospital/clinic priority, emergency bed count is not used as the main signal.

This keeps common symptoms such as mild cold from being forced into emergency routing.
