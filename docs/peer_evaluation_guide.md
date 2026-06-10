# 상대팀 평가 대응 가이드

이 문서는 상대팀 평가 기준에 맞춰 프로젝트의 강점과 증거 파일을 빠르게 확인할 수 있도록 정리한 발표/제출용 안내 문서다.

## 1. 문제 정의 명확성

### 분석 목적

본 프로젝트의 목적은 단순 병원 검색이 아니라, 사용자가 자연어로 입력한 증상을 기반으로 다음 정보를 단계적으로 안내하는 것이다.

1. 증상군 분류
2. 추천 진료과 예측
3. 의심 질환 TOP3 후보 산출
4. 필요한 추가 문진 질문 선택
5. 최종 응급도 계산
6. 응급 또는 상시 병원 추천

### 문제 유형과 선택한 방법

- 문제 유형: 자연어 텍스트 다중 분류 + 규칙 기반 위험도 보정 + 병원 추천 시스템
- 모델링: 네이버 지식인 증상 사례 기반 `symptom_classifier.pkl`
- 보조 규칙: red flag rule, triage risk score
- 추천: 진료과, 응급 여부, 병상, 거리/ETA를 함께 반영

### 평가 시 강조 문장

> 이 시스템은 질병 확정 진단기가 아니라, 자연어 증상 입력을 바탕으로 응급도와 적절한 병원 유형을 안내하는 의사결정 보조 시스템입니다.

## 2. 데이터 이해도

### 사용 데이터

| 데이터 | 역할 |
| --- | --- |
| `data/processed/naver_kin_symptom_cases_mapped.csv` | 모델 학습용 자연어 증상 사례 |
| `data/disease_master.csv` | 질환명, 별칭, disease_id 통합 기준 |
| `data/processed/disease_question_map_mapped.csv` | 질환별 추가 문진 후보 |
| `data/processed/triage_rule_dataset_mapped.csv` | 위험도 계산 보조 데이터 |
| `data/processed/hospital_master.csv` | 병원 추천용 병원 기본 정보 |
| `data/processed/gangwon_hospital_with_beds.csv` | 병상 fallback 데이터 |

### 현재 데이터 규모

- `disease_master.csv`: 149개 질환
- 네이버 증상 사례 mapped rows: 3,499건
- 학습 대상 disease_id: 118개
- 문진 질문 rows: 532개
- 문진 질문 disease_id: 121개
- 응급 rule disease_id: 101개
- mapped CSV unmapped row: 0개

### 주요 특징

- `suspected_disease` 문자열만 쓰지 않고 `disease_id`를 부여해 라벨 흔들림을 줄였다.
- 응급도 데이터는 질환 판단용이 아니라 risk score 보조용으로 분리했다.
- 비응급 일반 증상과 red flag 응급 증상을 함께 다룬다.
- 유사 사례는 예측 질환과 같은 사례를 우선 검색한다.

## 3. 기술 난이도

### 직접 설계/구현한 부분

- 네이버 지식인 기반 자연어 증상 데이터셋 구성
- `disease_master.csv`와 mapped CSV 파이프라인 구현
- `symptom_classifier.pkl` 학습 및 disease_id 모델 추가
- 질환별 문진 질문 랭킹 로직 구현
- 사용자 입력에 이미 포함된 정보는 다시 묻지 않는 중복 질문 제거
- red flag 우선 적용 로직
- 응급도별 응급/상시 병원 추천 분기
- 가용 병상 0개 병원 패널티 반영
- 카카오 경로 URL/ETA 구조 반영
- FastAPI + Next.js 통합 웹 서비스 구현

### 단순 API 호출이 아닌 이유

API는 병원 위치/경로/실시간 데이터 보조에 사용된다. 핵심 판단은 외부 LLM/API가 아니라 프로젝트 내부 데이터와 모델, 직접 구현한 fallback/ranking/recommendation 로직으로 수행한다.

## 4. 모델/시스템 완성도

### 모델 학습 과정

학습 스크립트:

```bash
python data_pipeline/symptom_model/train_symptom_classifier.py
```

모델 파일:

```text
models/symptom_classifier.pkl
```

모델 출력:

- `symptom_group`
- `department`
- `suspected_disease`
- `disease_id`
- disease TOP3 candidates

### 모델 성능 비교

비교 근거:

- `docs/symptom_classifier_evaluation.md`
- `data/processed/model_evaluation/model_comparison_summary.csv`
- `data/processed/model_evaluation/*classification_report.csv`

비교 모델:

- Majority baseline
- Word TF-IDF + Logistic Regression
- Character n-gram TF-IDF + Logistic Regression
- Character n-gram TF-IDF + Linear SVC

### 시스템 완성도

시스템은 다음 흐름을 하나로 연결한다.

```text
사용자 증상 입력
-> 모델 기반 질환/진료과/증상군 예측
-> disease_id 기반 문진 질문 선택
-> 사용자 답변 반영
-> 최종 증상 문장 재분석
-> 응급도 계산
-> 병원 추천
-> 유사 사례와 원문 링크 제공
```

## 5. 실제 검증 결과

최종 검증 보고서:

- `reports/final_system_validation_report.md`

검증 결과:

- 모델 로드: PASS
- disease_id 예측: PASS
- confidence 범위: PASS
- disease_master 로딩: PASS
- mapped CSV 로딩/매핑: PASS
- backend import: PASS
- symptom analyzer/triage service 실행: PASS
- smoke test: PASS
- FastAPI 실제 실행: PASS
- `/api/health`: PASS
- `/api/triage/questions`: PASS
- `/api/triage/analyze`: PASS

배포 사이트 수동/브라우저 검증:

- 사이트 접속 정상
- 문진 질문 출력 정상
- 뇌졸중 예시 최종 결과 정상
- 추천 병원, 병상, 예상 이동시간, 카카오맵 경로 링크 표시 정상

## 6. 발표용 추천 데모

자세한 TOP10:

- `reports/demo_scenarios_top10.md`

가장 안정적인 데모 5개:

1. `갑자기 왼팔에 힘이 안 들어가고 말이 어눌해요`
   - 뇌졸중, 신경과, 긴급, 응급의료기관 추천
2. `가슴을 짓누르는 통증과 식은땀이 납니다`
   - 급성 심근경색, 응급, 병상 기반 병원 추천
3. `벌에 쏘인 뒤 입술이 붓고 숨쉬기 힘듭니다`
   - 아나필락시스, red flag, 응급 안내
4. `설사를 6번 정도 했고 복통이 있습니다`
   - 장염/소화기, 문진 질문, 상시 병원 추천
5. `목이 아프고 콧물이 나며 기침이 있습니다. 열은 37.5도 정도입니다`
   - 감기, 낮은 응급도, 상시 병원 추천

## 7. 남은 한계와 방어 답변

### 한계

- 의료진 확정 진단 수준의 정답성은 보장하지 않는다.
- 네이버 지식인 데이터는 사용자 표현 데이터이므로 정식 의료 정답셋과 다르다.
- 실시간 병상/ETA는 외부 API 상태와 키 설정에 영향을 받는다.
- 일부 짧거나 모호한 입력은 fallback rule 의존도가 높다.

### 방어 답변

> 본 프로젝트의 목표는 의학적 확정 진단이 아니라, 자연어 증상을 기반으로 응급도와 병원 선택을 돕는 데이터마이닝 기반 안내 시스템입니다. 따라서 모델 결과는 TOP3 후보로 제공하고, 생명 위험 red flag는 모델 confidence와 무관하게 우선 적용하도록 설계했습니다.

## 8. 상대팀이 보기 쉬운 핵심 증거 파일

- 문제 정의/구조: `docs/system_architecture_v2.md`
- 모델 구조: `docs/model_design_v2.md`
- disease master: `docs/disease_master_design.md`
- 모델 평가: `docs/symptom_classifier_evaluation.md`
- 최종 검증: `reports/final_system_validation_report.md`
- 발표 시나리오: `reports/demo_scenarios_top10.md`
- 발표 준비도: `reports/final_presentation_readiness.md`
- 저장소 정리: `docs/repository_cleanup_report.md`

## 9. 최종 자기평가

상대팀 평가 기준 기준으로 다음 근거를 제시할 수 있다.

| 기준 | 자기평가 | 핵심 근거 |
| --- | --- | --- |
| 문제 정의 명확성 | 높음 | 자연어 증상 입력에서 응급도/병원 안내까지 문제 흐름이 명확함 |
| 데이터 이해도 | 높음 | 질환/질문/응급룰/병원 데이터를 disease_id 중심으로 통합 |
| 기술 난이도 | 높음 | 단순 API가 아니라 모델, fallback, 추천 로직을 직접 구현 |
| 모델/시스템 완성도 | 높음 | 실제 배포 사이트, API, smoke test, 최종 검증 PASS |

