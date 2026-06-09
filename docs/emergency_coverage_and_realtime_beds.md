# Emergency Coverage And Realtime Beds

## Why This Was Added

The original classifier was trained on a narrow set of suspected diseases. When a user entered symptoms outside that label space, the model had to force the input into one of the existing labels. That caused cases such as concussion, norovirus-like gastroenteritis, or fever with breathing difficulty to be mapped to unrelated labels.

This upgrade adds a wider emergency disease label master and a crawl query plan so the dataset can be expanded systematically instead of patching individual examples only.

## Generated Data Files

- `data/processed/emergency_disease_label_master.csv`
  - Curated emergency disease and situation labels.
  - Includes symptom group, department, severity, and search keywords.

- `data/processed/naver_crawl_query_plan.csv`
  - Search query plan for future Naver Knowledge iN crawling.
  - Each row maps a disease label to a query and target collection count.

- `data/processed/disease_question_map.csv`
  - Expanded so labels outside the original 27-disease dataset can still receive disease-specific follow-up questions.

- `data/processed/triage_rule_dataset.csv`
  - Expanded with fallback high-risk rules for the wider emergency label space.

Run:

```bash
python -X utf8 data_pipeline/symptom_model/expand_emergency_coverage.py
```

## Realtime Bed API

The backend now tries to fetch realtime emergency bed counts from the National Emergency Medical Center public data API before falling back to the static CSV.

Environment variable names checked:

```bash
EGEN_API_KEY
PUBLIC_DATA_SERVICE_KEY
DATA_GO_KR_SERVICE_KEY
```

If no key is configured or the API call fails, `gangwon_hospital_with_beds.csv` remains the fallback.

The hospital recommendation response includes:

- `available_beds`
- `bed_source`
  - `egen_realtime`
  - `static_csv`
- `bed_updated_at`

## Public Data Source

The public data source is `국립중앙의료원_전국 응급의료기관 정보 조회 서비스` on the Korean Public Data Portal. The portal describes it as providing realtime emergency room available bed information and severe emergency disease acceptance information.
