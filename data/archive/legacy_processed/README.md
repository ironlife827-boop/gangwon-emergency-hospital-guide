# Legacy Processed Data

This folder stores processed data snapshots and intermediate files that are not loaded by the current production backend.

## Current Active Data

The app currently reads these files directly at runtime:

- `data/processed/naver_kin_symptom_cases.csv`
- `data/processed/disease_question_map.csv`
- `data/processed/triage_rule_dataset.csv`
- `data/processed/hospital_master.csv`
- `data/processed/gangwon_hospital_with_beds.csv`
- `models/symptom_classifier.pkl`
- `models/eta_model.pkl`

The training/evaluation pipeline also uses:

- `data/processed/naver_kin_symptom_cases.csv`
- `data/processed/naver_crawl_query_plan.csv`
- `data/processed/emergency_disease_label_master.csv`
- `data/processed/model_evaluation/*.csv`

## Archived Files

- `eta_training_dataset.csv`: old ETA model training data; the running service loads `models/eta_model.pkl`.
- `hospital_distance.csv`: old distance table; current recommendations calculate distance from user coordinates.
- `naver_kin_expanded_crawled_raw.csv`: raw crawl output from the previous expansion run.
- `naver_kin_expanded_crawled_filtered.csv`: filtered crawl output from the previous expansion run.
- `naver_kin_symptom_cases_expanded.csv`: previous expanded dataset output, superseded by `naver_kin_symptom_cases.csv`.
- `naver_kin_symptom_cases.before_expansion.csv`: backup snapshot before expansion.
- `naver_kin_removed_rows.csv`: rows removed during older cleaning runs.
- `naver_kin_label_summary.csv`: older label summary snapshot.

These files are kept for audit/history only. Move them back to `data/processed/` only when reproducing an old pipeline run.
