# Legacy Models

This folder stores model artifacts that are not loaded by the current production backend.

- `severity_model.pkl`: old emergency severity model. Current severity calculation uses `disease_question_map.csv` and `triage_rule_dataset.csv` risk scores with deterministic clamping, while disease prediction uses `models/symptom_classifier.pkl`.

Keep this file only for history or comparison. The running app should not depend on it.
