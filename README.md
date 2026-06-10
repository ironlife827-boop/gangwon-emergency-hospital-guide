# Gangwon Emergency Hospital Guide

강원도 맞춤형 응급 및 상시 병원 안내 웹 서비스입니다.

사용자가 자연어로 증상을 입력하면 네이버 지식인 기반 증상 사례 데이터로 학습한 모델이 증상군, 추천 진료과, 의심 질환을 예측합니다. 이후 질환별 추가 문진을 1~4개만 선택하고, 최종 응급도와 추천 병원을 보여줍니다.

## Evaluation Quick Links

상대팀 평가 또는 최종 발표에서 먼저 확인하면 좋은 문서입니다.

- `docs/peer_evaluation_guide.md`: 상대팀 평가 기준별 대응 근거
- `reports/final_system_validation_report.md`: 모델 로드, backend 실행, API, mapped CSV 검증 결과
- `reports/demo_scenarios_top10.md`: 발표용 추천 증상 시나리오 TOP10
- `reports/final_presentation_readiness.md`: 최종 발표 준비도, 예상 질문 TOP20
- `docs/repository_cleanup_report.md`: 실제 사용 파일과 archive 파일 정리 결과

## Project Highlights

- 단순 병원 검색이 아니라 `증상 입력 -> 모델 예측 -> 추가 문진 -> 응급도 계산 -> 병원 추천` 흐름을 하나의 시스템으로 구현했습니다.
- 질환 판단은 `models/symptom_classifier.pkl`이 중심이며, 응급도 데이터는 risk score 계산 보조로 사용합니다.
- `data/disease_master.csv`와 mapped CSV를 사용해 질환명을 `disease_id` 기준으로 통합했습니다.
- 문진 질문은 새로 생성하지 않고 `disease_question_map_mapped.csv`의 후보를 랭킹해 선택합니다.
- red flag 증상은 모델 confidence와 무관하게 안전 우선으로 응급도를 보정합니다.
- 비응급 증상은 상시 병원, 응급 증상은 응급의료기관 중심으로 추천합니다.

## Core Flow

1. 사용자 자연어 증상 입력
2. `models/symptom_classifier.pkl`로 `symptom_group`, `department`, `suspected_disease` 예측
3. `data/processed/disease_question_map.csv`에서 질환별 질문 후보 로드
4. 질환 일치, 증상군 일치, 위험도, 중요도, 중복 여부로 질문 랭킹
5. 최초 증상과 문진 답변을 합쳐 최종 증상 문장 생성
6. 최종 증상 문장을 다시 분류 모델에 넣어 질환 재판정
7. 위험 점수 계산 후 추천 병원 출력

## Main Directories

- `backend/`: FastAPI backend
- `frontend/`: Next.js frontend
- `data/processed/`: cleaned datasets, question map, hospital data, evaluation outputs
- `data_pipeline/symptom_model/`: symptom classifier training and evaluation scripts
- `models/`: trained model artifacts
- `docs/`: project evaluation, model evaluation, realtime ETA notes
- `archive/legacy/`: old patch snapshots, unused scaffold assets, and experimental code kept for reference

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Optional realtime route ETA:

```bash
KAKAO_MOBILITY_REST_API_KEY=your_key
```

If the key is missing, the service falls back to the existing ETA model.

## Frontend

```bash
cd frontend
npm ci
npm run dev
```

Optional API endpoint override:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api.example.com
```

## Model Evaluation

Run model comparison:

```bash
python data_pipeline/symptom_model/evaluate_symptom_classifier.py
```

Evaluation outputs:

- `docs/symptom_classifier_evaluation.md`
- `data/processed/model_evaluation/model_comparison_summary.csv`

## Validation Commands

```bash
python -m py_compile backend/services/triage_service.py backend/services/recommendation_service.py backend/services/eta_service.py
cd frontend
npm run lint
npm run build
```

Full final validation:

```bash
python -X utf8 scripts/final_system_validation.py
python -X utf8 scripts/generate_demo_scenarios.py
```

Smoke test:

```bash
python -X utf8 data_pipeline/symptom_model/smoke_test_triage_quality.py
```

## Notes

- Disease prediction is handled by the trained classifier, not by triage rules.
- `triage_rule_dataset.csv` is used only as fallback and risk-score support.
- LLM-related legacy code is archived and is not part of the current runtime.
