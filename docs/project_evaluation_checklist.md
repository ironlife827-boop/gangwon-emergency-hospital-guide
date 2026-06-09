# 프로젝트 평가 기준 대응표

## 1. 문제 정의 명확성

### 분석 목적

사용자가 자연어로 입력한 증상 문장을 기반으로 다음 정보를 예측하고 안내한다.

1. 증상군
2. 추천 진료과
3. 의심 질환
4. 필요한 추가 문진
5. 최종 응급도
6. 강원도 내 추천 병원

핵심 문제는 단순 병원 검색이 아니라 `증상 자연어 -> 의심 질환/진료과 -> 응급도 -> 병원 추천`으로 이어지는 중간 판단 시스템을 구현하는 것이다.

### 문제 유형과 방법 선택

- 문제 유형: 다중 클래스 텍스트 분류 + 규칙 기반 위험도 보정 + 병원 추천 시스템
- 주요 방법:
  - 네이버 지식인 기반 증상 사례 데이터 수집/정제
  - `cleaned_text`, `symptom_keywords` 기반 TF-IDF 분류 모델 학습
  - `symptom_group`, `department`, `suspected_disease`를 각각 예측
  - 질환별 문진 질문 DB에서 동적 질문 선택
  - 위험 점수 기반 응급도 계산
  - 진료과, 응급도, 위치, 병상 정보를 반영한 병원 추천

## 2. 데이터 이해도

### 기초 통계

- 데이터 파일: `data/processed/naver_kin_symptom_cases.csv`
- 전체 사례 수: 3,139건
- 증상군 수: 15개
- 진료과 수: 14개
- 의심 질환 수: 76개
- 질환별 문진 질문: 81개 질환, 397개 문항 확보
- `naver_crawl_query_plan.csv` 기준 추가 수집 후보 450건 중 432건을 필터 통과 데이터로 반영

자세한 분포와 모델 비교 결과는 `docs/symptom_classifier_evaluation.md`에 정리되어 있다.

### 주요 특징

- 자연어 원문(`raw_text`)과 정제 문장(`cleaned_text`)을 분리했다.
- 증상 핵심어(`symptom_keywords`)를 별도 컬럼으로 구성해 학습 입력에 함께 사용한다.
- 질환 판단용 라벨(`suspected_disease`)과 응급도 보조 라벨(`severity_level`)을 분리했다.
- 응급 문진 데이터(`triage_rule_dataset.csv`)는 질환 분류가 아니라 위험도 계산 보조용으로 사용한다.
- 동물, 꿈, 법률, 광고, 비의료성 사례는 학습 데이터에 들어가지 않도록 필터링했다.

## 3. 기술 난이도

### 직접 설계/구현한 부분

- 네이버 지식인 기반 증상 사례 CSV 구조 설계
- 증상군/진료과/의심 질환 라벨 구성
- `symptom_classifier.pkl` 학습 파이프라인 구현
- 질환별 동적 추가 문진 로직 구현
- 모든 `suspected_disease`를 커버하는 `disease_question_map.csv` 보강
- 사용자 최초 증상과 문진 답변을 합친 최종 재분류 로직 구현
- 응급도 계산과 병원 추천 연결
- 프론트엔드 입력/문진/결과 출력 흐름 구현

### 단순 API 호출이 아닌 이유

- 질환 판단은 외부 LLM/API가 아니라 프로젝트 내부의 학습 모델(`symptom_classifier.pkl`)이 수행한다.
- LLM은 핵심 판단 로직에 의존하지 않고, 필요 시 보조 도구로만 활용하는 구조다.
- 병원 추천 역시 단순 검색 API가 아니라 진료과, 응급도, 위치, 병상 정보를 조합한다.

## 4. 모델/시스템 완성도

### 모델 학습 과정

- 학습 스크립트: `data_pipeline/symptom_model/train_symptom_classifier.py`
- 평가 스크립트: `data_pipeline/symptom_model/evaluate_symptom_classifier.py`
- 저장 모델: `models/symptom_classifier.pkl`
- 입력 특징:
  - `cleaned_text`
  - `symptom_keywords`
- 예측 대상:
  - `symptom_group`
  - `department`
  - `suspected_disease`

### 모델 성능 비교

비교한 모델:

- Majority-class baseline
- Word TF-IDF + Logistic Regression
- Character n-gram TF-IDF + Logistic Regression
- Character n-gram TF-IDF + Linear SVC

요약 결과:

| Target | Best model | Accuracy | Macro F1 |
| --- | --- | ---: | ---: |
| symptom_group | char_tfidf_linear_svc | 0.9809 | 0.9700 |
| department | char_tfidf_linear_svc | 0.9841 | 0.9680 |
| suspected_disease | char_tfidf_linear_svc | 0.9857 | 0.9410 |

상세 결과:

- `data/processed/model_evaluation/model_comparison_summary.csv`
- `data/processed/model_evaluation/symptom_group_best_model_classification_report.csv`
- `data/processed/model_evaluation/department_best_model_classification_report.csv`
- `data/processed/model_evaluation/suspected_disease_best_model_classification_report.csv`
- `docs/symptom_classifier_evaluation.md`

### 시스템 완성도

현재 시스템 흐름:

1. 사용자가 자연어 증상 입력
2. `symptom_classifier.pkl`로 증상군/진료과/의심 질환 예측
3. `disease_question_map.csv`에서 예측 질환 중심으로 질문 후보 로드
4. 질환 일치, 증상군 일치, 위험도, 중요도, 중복 정보를 기준으로 질문 랭킹
5. 필요한 질문 1~4개만 출력
6. 최초 증상과 문진 답변을 합쳐 최종 증상 문장 생성
7. 최종 증상 문장을 다시 모델에 넣어 질환 재판정
8. 위험 점수를 10점 만점으로 계산
9. 응급도, 의심 질환, 진료과, 추천 병원 출력
10. 유사 사례와 네이버 원문 링크 제공
11. 병원 추천은 거리뿐 아니라 가용 병상, 응급실 여부, 진료과 매칭, 예상 이동시간을 함께 반영

## 5. 현재 기준 부족하거나 주의할 점

### 보강 완료

- 모델 비교 평가 결과 추가
- 데이터 기초 통계 문서화
- 질환별 문진 질문 DB 커버리지 보강
- 교수님 피드백의 핵심인 `증상 -> 과/질환 매칭 모델` 구현
- 대표 오분류 사례를 회귀 테스트로 추가
- 가용 병상 0개 병원이 거리만으로 우선 추천되지 않도록 병상 우선순위 보강
- 해산물 단서가 없는 고열/두통 사례가 노로바이러스나 열사병으로 과도하게 보정되지 않도록 앵커 조건 보강

### 남은 리스크

- 현재 평가는 같은 출처의 데이터에서 train/test split을 한 결과다.
- 실제 사용자 문장과 네이버 지식인 문장 분포가 다를 수 있다.
- 향후 별도의 사람 검수 테스트셋을 만들면 평가 신뢰도가 더 높아진다.
- 현재 운영 모델은 안정성과 속도를 위해 TF-IDF 기반 모델을 사용한다. Transformer 모델은 추후 고도화 후보로 남겨두었다.
- 최종 응급도 단계는 1단계가 가장 긴급하고, 원자료의 `severity_level`은 5가 가장 위험한 보조 라벨이다. 화면에서는 최종 응급도와 유사 사례 위험도를 구분해 표시한다.

## 결론

현재 프로젝트는 평가 기준의 핵심 항목을 대부분 충족한다.

특히 기존 약점이었던 `증상 자연어 입력과 병원 추천 사이의 중간 모델 연결`이 구현되었고, 모델 비교 평가와 데이터 통계 문서까지 추가되어 발표/보고서에서 근거를 제시할 수 있는 상태다.
