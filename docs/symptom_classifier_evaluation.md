# Symptom Classifier Evaluation

## Purpose

This report documents the model-centered link in the service: natural-language symptom text is mapped to `symptom_group`, `department`, and `suspected_disease` before triage questions and hospital recommendations are generated.

The emergency triage rule data is not used as the disease classifier. It is used later as a risk-score aid.

## Dataset

- Source: `data/processed/naver_kin_symptom_cases.csv`
- Rows used: 3139
- Input features: `cleaned_text` + `symptom_keywords`
- Targets:
  - `symptom_group`: 15 classes
  - `department`: 14 classes
  - `suspected_disease`: 76 classes
- Train/test split: 80% / 20%, stratified by each target

## Model Comparison

Compared models:

- `baseline_most_frequent`: majority-class baseline
- `word_tfidf_logreg`: word unigram/bigram TF-IDF + Logistic Regression
- `char_tfidf_logreg`: character n-gram TF-IDF + Logistic Regression
- `char_tfidf_linear_svc`: character n-gram TF-IDF + Linear SVC

| Target | Model | Accuracy | Macro F1 | Weighted F1 | Classes |
| --- | --- | --- | --- | --- | --- |
| symptom_group | baseline_most_frequent | 0.2723 | 0.0285 | 0.1166 | 15 |
| symptom_group | word_tfidf_logreg | 0.9618 | 0.9350 | 0.9638 | 15 |
| symptom_group | char_tfidf_logreg | 0.9427 | 0.8906 | 0.9494 | 15 |
| symptom_group | char_tfidf_linear_svc | 0.9809 | 0.9700 | 0.9809 | 15 |
| department | baseline_most_frequent | 0.4793 | 0.0463 | 0.3106 | 14 |
| department | word_tfidf_logreg | 0.9570 | 0.9180 | 0.9616 | 14 |
| department | char_tfidf_logreg | 0.9379 | 0.8603 | 0.9452 | 14 |
| department | char_tfidf_linear_svc | 0.9841 | 0.9680 | 0.9845 | 14 |
| suspected_disease | baseline_most_frequent | 0.0350 | 0.0009 | 0.0024 | 76 |
| suspected_disease | word_tfidf_logreg | 0.9793 | 0.9450 | 0.9797 | 76 |
| suspected_disease | char_tfidf_logreg | 0.9745 | 0.9050 | 0.9730 | 76 |
| suspected_disease | char_tfidf_linear_svc | 0.9857 | 0.9410 | 0.9851 | 76 |

## Best Model By Target

| Target | Best Model | Accuracy | Macro F1 | Weighted F1 |
| --- | --- | --- | --- | --- |
| symptom_group | char_tfidf_linear_svc | 0.9809 | 0.9700 | 0.9809 |
| department | char_tfidf_linear_svc | 0.9841 | 0.9680 | 0.9845 |
| suspected_disease | word_tfidf_logreg | 0.9793 | 0.9450 | 0.9797 |

## Data Understanding

### Symptom Group Distribution

| Symptom Group | Rows |
| --- | --- |
| toxic | 856 |
| trauma | 472 |
| respiratory | 355 |
| cardio | 324 |
| bleeding | 300 |
| abdominal | 240 |
| allergy | 216 |
| neuro | 132 |
| eye | 124 |
| urology | 24 |
| pediatric | 24 |
| obgy | 24 |
| psychiatric | 24 |
| foreign_body | 16 |
| infection | 8 |

### Department Distribution

| Department | Rows |
| --- | --- |
| 응급의학과 | 1507 |
| 호흡기내과 | 332 |
| 정형외과 | 308 |
| 소화기내과 | 224 |
| 알레르기내과 | 216 |
| 심장내과 | 208 |
| 안과 | 124 |
| 신경과 | 116 |
| 비뇨의학과 | 24 |
| 소아청소년과 | 24 |
| 산부인과 | 24 |
| 정신건강의학과 | 16 |
| 외과 | 8 |
| 이비인후과 | 8 |

### Suspected Disease Distribution

| Suspected Disease | Rows |
| --- | --- |
| 아나필락시스 | 108 |
| 열사병 | 108 |
| 일산화탄소중독 | 108 |
| 저체온증 | 108 |
| 화학물질중독 | 108 |
| 간부전 | 100 |
| 객혈 | 100 |
| 골절 | 100 |
| 급성 시력상실 | 100 |
| 급성 심근경색 | 100 |
| 기도폐쇄 | 100 |
| 뇌졸중 | 100 |
| 대량출혈 | 100 |
| 독사교상 | 100 |
| 벌쏘임 | 100 |
| 복막염 | 100 |
| 부정맥 | 100 |
| 신부전 | 100 |
| 심정지 | 100 |
| 약물중독 | 100 |
| 위장관출혈 | 100 |
| 익수 | 100 |
| 장폐색 | 100 |
| 전기손상 | 100 |
| 질식 | 100 |
| 탈구 | 100 |
| 화상 | 100 |
| 고열 동반 호흡곤란 | 15 |
| 뇌진탕 의심 두부손상 | 8 |
| 외상성 뇌손상 | 8 |
| 경추손상 | 8 |
| 척추손상 | 8 |
| 다발성외상 | 8 |
| 개방성 골절 | 8 |
| 절단손상 | 8 |
| 압궤손상 | 8 |
| 안면외상 | 8 |
| 폐렴 의심 고열 | 8 |
| 천식 악화 | 8 |
| COPD 급성악화 | 8 |
| 기흉 | 8 |
| 폐색전증 | 8 |
| 급성 심부전 | 8 |
| 대동맥박리 | 8 |
| 고혈압성 응급 | 8 |
| 실신 | 8 |
| 경련 발작 | 8 |
| 수막염 의심 | 8 |
| 편두통 위험징후 | 8 |
| 급성 충수염 | 8 |
| 담낭염 | 8 |
| 요로결석 | 8 |
| 급성 신우신염 | 8 |
| 고환염전 | 8 |
| 노로바이러스 의심 급성 위장염 | 8 |
| 식중독 | 8 |
| 중증 탈수 | 8 |
| 저혈당 | 8 |
| 고혈당성 응급 | 8 |
| 패혈증 의심 | 8 |
| 열성경련 | 8 |
| 영아 호흡곤란 | 8 |
| 소아 탈수 | 8 |
| 임신 중 복통출혈 | 8 |
| 자궁외임신 의심 | 8 |
| 분만 임박 | 8 |
| 자살위험 | 8 |
| 공황발작 | 8 |
| 섬망 의심 | 8 |
| 눈 화학손상 | 8 |
| 망막박리 의심 | 8 |
| 각막손상 | 8 |
| 기도 이물 | 8 |
| 식도 이물 | 8 |
| 혈관부종 | 8 |
| 알코올중독 | 8 |

## System Interpretation

The production service prioritizes `symptom_classifier.pkl` for disease and department prediction. After prediction, `disease_question_map.csv` selects disease-specific follow-up questions. Final analysis merges the initial symptom with follow-up answers and runs the classifier again before calculating emergency risk and recommending hospitals.

## Limitations And Next Improvements

- The current dataset is intentionally balanced by suspected disease in the latest processed CSV, which helps model training but may differ from real-world symptom frequency.
- Evaluation uses a held-out split from the same source distribution. A future improvement is to collect a separate human-labeled validation set.
- Transformer fine-tuning is documented separately as a future path, but the current deployed system uses lightweight TF-IDF models for stability and fast inference.
