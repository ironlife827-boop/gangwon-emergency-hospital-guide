# Final System Validation Report

- Generated at: 2026-06-10 09:31:03
- Overall: PASS
- Passed: 21
- Failed: 0

## Test Results

| Test | Status | Details |
| --- | --- | --- |
| model keys | PASS | dict_keys(['symptom_group_model', 'department_model', 'disease_model', 'disease_id_model', 'metadata']) |
| disease_id prediction | PASS | 갑자기 왼팔에 힘이 안 들어가고 말이 어눌해요 -> D_NEU_003 / neuro |
| confidence range | PASS | top1 confidence=0.1054 |
| disease_master columns | PASS |  |
| disease_master unique disease_id | PASS |  |
| disease_master unique disease_name | PASS |  |
| naver_kin_symptom_cases_mapped.csv mapping | PASS | rows=3499, disease_ids=118, unknown=0 |
| disease_question_map_mapped.csv mapping | PASS | rows=532, disease_ids=121, unknown=0 |
| triage_rule_dataset_mapped.csv mapping | PASS | rows=113, disease_ids=101, unknown=0 |
| emergency_disease_label_master_mapped.csv mapping | PASS | rows=54, disease_ids=54, unknown=0 |
| load_disease_master | PASS | rows=149 |
| load_naver_cases | PASS | rows=3499 |
| load_disease_questions | PASS | rows=532 |
| load_triage_rules | PASS | rows=113 |
| symptom_engine current service | PASS | 감기 / respiratory / candidates=3 |
| question selection | PASS | 급성 심근경색 / questions=3 |
| triage analyze service | PASS | 감기 / severity=5 / hospitals=3 |
| smoke test | PASS | returncode=0, fail_lines=0 |
| backend uvicorn runtime | PASS | {"ok": true, "message": "backend is running"} |
| api /triage/questions | PASS | status=200, disease=뇌졸중, questions=2 |
| api /triage/analyze | PASS | status=200, disease=감기, hospitals=3 |

## Failed Items

- None

## Fixes Applied During Final Validation

- Added repeatable final validation coverage for model loading, mapped CSV integrity, service imports, smoke tests, and live FastAPI endpoints.
- Confirmed the current symptom engine is implemented by `backend/services/symptom_analyzer.py` and `backend/services/triage_service.py`; no separate `symptom_engine_v2.py` runtime file exists.

## Remaining Risks

- This is a decision-support demo, not a medical diagnosis system.
- The model still depends on synthetic and crawled symptom text quality; rare phrasing can require fallback rules.
- Realtime bed/ETA quality depends on external API keys and public data freshness.
- Some legacy Korean text in source comments/README appears mojibake in the current checkout and should be explained as an encoding artifact if noticed.

## Presentation Notes

- Emphasize that disease prediction is TOP3 candidate support, while red flags override model confidence for safety.
- Show both a non-emergency primary-care case and an emergency red-flag case.
- State clearly that triage rules are used for risk scoring, not as the main disease classifier.
