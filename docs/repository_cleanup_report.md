# Repository Cleanup Report

## Summary

최종 런타임 기준으로 사용하는 파일과 과거 실험/레거시 파일을 분리했다. 실제 서비스가 읽는 모델, CSV, 백엔드/프론트엔드 코드는 유지했고, 이미 보관 성격이던 실험 코드와 legacy 데이터/모델은 `archive/` 하위 정책 폴더로 이동했다.

## 유지 파일 목록

- `backend/main.py`
- `backend/routers/*.py`
- `backend/schemas/*.py`
- `backend/services/data_loader.py`
- `backend/services/symptom_analyzer.py`
- `backend/services/triage_service.py`
- `backend/services/recommendation_service.py`
- `backend/services/eta_service.py`
- `backend/services/realtime_bed_service.py`
- `backend/services/location_service.py`
- `frontend/app/page.tsx`
- `frontend/app/layout.tsx`
- `frontend/app/globals.css`
- `frontend/public/app-icon.png`
- `models/symptom_classifier.pkl`
- `models/eta_model.pkl`
- `data/disease_master.csv`
- `data/processed/naver_kin_symptom_cases_mapped.csv`
- `data/processed/disease_question_map_mapped.csv`
- `data/processed/triage_rule_dataset_mapped.csv`
- `data/processed/emergency_disease_label_master_mapped.csv`
- `data/processed/hospital_master.csv`
- `data/processed/gangwon_hospital_with_beds.csv`
- `data_pipeline/disease_master/*.py`
- `data_pipeline/symptom_model/train_symptom_classifier.py`
- `data_pipeline/symptom_model/smoke_test_triage_quality.py`
- `scripts/final_system_validation.py`
- `scripts/generate_demo_scenarios.py`

## archive 이동 파일 목록

- `archive/legacy/experimental-transformer/` -> `archive/experimental/experimental-transformer/`
- `archive/legacy/unused-services/` -> `archive/experimental/unused-services/`
- `models/archive/legacy_models/` -> `archive/models/legacy_models/`
- `data/archive/legacy_processed/` -> `archive/data/legacy_processed/`

## 유지한 과거 참고 자료

다음 파일은 런타임에는 직접 사용하지 않지만, 발표/재현성/평가 근거로 가치가 있어 유지한다.

- `data/raw/naver_kin_raw_text.xlsx`
- `data/processed/naver_crawl_query_plan.csv`
- `data/processed/model_evaluation/*.csv`
- `docs/symptom_classifier_evaluation.md`
- `docs/final_completion_review.md`
- `docs/project_evaluation_checklist.md`
- `docs/disease_master_design.md`
- `docs/model_design_v2.md`
- `docs/system_architecture_v2.md`

## 제거 가능한 파일 목록

즉시 삭제하지는 않았다. 제출 직전 용량이나 혼동을 줄여야 할 경우에만 아래를 삭제 후보로 검토할 수 있다.

- `archive/legacy/patch-snapshots/`
- `archive/legacy/frontend-default-assets/`
- `archive/experimental/experimental-transformer/`
- `archive/experimental/unused-services/`
- `archive/data/legacy_processed/`
- `archive/models/legacy_models/`

## 실제 서비스 핵심 파일

현재 서비스 동작의 핵심은 아래 흐름이다.

1. `models/symptom_classifier.pkl`
2. `data/disease_master.csv`
3. `data/processed/*_mapped.csv`
4. `backend/services/symptom_analyzer.py`
5. `backend/services/triage_service.py`
6. `backend/services/recommendation_service.py`
7. `frontend/app/page.tsx`

## 정리 후 판단

- 런타임 파일과 archive 파일이 분리되어 GitHub 제출 시 설명하기 쉬워졌다.
- 기존 원본 CSV와 학습/평가 근거는 삭제하지 않아 재현성과 발표 근거를 유지했다.
- 불필요한 legacy 모델이 `models/` 루트에서 빠져 현재 사용 모델이 더 명확해졌다.
