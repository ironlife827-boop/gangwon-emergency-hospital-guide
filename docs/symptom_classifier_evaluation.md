# Symptom Classifier Evaluation

## Purpose

This report documents the model-centered link in the service: natural-language symptom text is mapped to `symptom_group`, `department`, and `suspected_disease` before triage questions and hospital recommendations are generated.

The emergency triage rule data is not used as the disease classifier. It is used later as a risk-score aid.

## Dataset

- Source: `data/processed/naver_kin_symptom_cases.csv`
- Rows used: 2700
- Input features: `cleaned_text` + `symptom_keywords`
- Targets:
  - `symptom_group`: 9 classes
  - `department`: 8 classes
  - `suspected_disease`: 27 classes
- Train/test split: 80% / 20%, stratified by each target

## Model Comparison

Compared models:

- `baseline_most_frequent`: majority-class baseline
- `word_tfidf_logreg`: word unigram/bigram TF-IDF + Logistic Regression
- `char_tfidf_logreg`: character n-gram TF-IDF + Logistic Regression
- `char_tfidf_linear_svc`: character n-gram TF-IDF + Linear SVC

| Target | Model | Accuracy | Macro F1 | Weighted F1 | Classes |
| --- | --- | --- | --- | --- | --- |
| symptom_group | baseline_most_frequent | 0.2963 | 0.0508 | 0.1354 | 9 |
| symptom_group | word_tfidf_logreg | 0.9870 | 0.9885 | 0.9871 | 9 |
| symptom_group | char_tfidf_logreg | 0.9870 | 0.9877 | 0.9871 | 9 |
| symptom_group | char_tfidf_linear_svc | 0.9926 | 0.9926 | 0.9926 | 9 |
| department | baseline_most_frequent | 0.4815 | 0.0812 | 0.3130 | 8 |
| department | word_tfidf_logreg | 0.9889 | 0.9905 | 0.9890 | 8 |
| department | char_tfidf_logreg | 0.9926 | 0.9939 | 0.9926 | 8 |
| department | char_tfidf_linear_svc | 0.9981 | 0.9987 | 0.9982 | 8 |
| suspected_disease | baseline_most_frequent | 0.0370 | 0.0026 | 0.0026 | 27 |
| suspected_disease | word_tfidf_logreg | 0.9870 | 0.9866 | 0.9866 | 27 |
| suspected_disease | char_tfidf_logreg | 0.9889 | 0.9888 | 0.9888 | 27 |
| suspected_disease | char_tfidf_linear_svc | 0.9907 | 0.9907 | 0.9907 | 27 |

## Best Model By Target

| Target | Best Model | Accuracy | Macro F1 | Weighted F1 |
| --- | --- | --- | --- | --- |
| symptom_group | char_tfidf_linear_svc | 0.9926 | 0.9926 | 0.9926 |
| department | char_tfidf_linear_svc | 0.9981 | 0.9987 | 0.9982 |
| suspected_disease | char_tfidf_linear_svc | 0.9907 | 0.9907 | 0.9907 |

## Data Understanding

### Symptom Group Distribution

| Symptom Group | Rows |
| --- | --- |
| toxic | 800 |
| trauma | 400 |
| bleeding | 300 |
| cardio | 300 |
| respiratory | 300 |
| allergy | 200 |
| abdominal | 200 |
| eye | 100 |
| neuro | 100 |

### Department Distribution

| Department | Rows |
| --- | --- |
| 응급의학과 | 1300 |
| 정형외과 | 300 |
| 호흡기내과 | 300 |
| 심장내과 | 200 |
| 알레르기내과 | 200 |
| 소화기내과 | 200 |
| 안과 | 100 |
| 신경과 | 100 |

### Suspected Disease Distribution

| Suspected Disease | Rows |
| --- | --- |
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
| 아나필락시스 | 100 |
| 약물중독 | 100 |
| 열사병 | 100 |
| 위장관출혈 | 100 |
| 익수 | 100 |
| 일산화탄소중독 | 100 |
| 장폐색 | 100 |
| 저체온증 | 100 |
| 전기손상 | 100 |
| 질식 | 100 |
| 탈구 | 100 |
| 화상 | 100 |
| 화학물질중독 | 100 |

## System Interpretation

The production service prioritizes `symptom_classifier.pkl` for disease and department prediction. After prediction, `disease_question_map.csv` selects disease-specific follow-up questions. Final analysis merges the initial symptom with follow-up answers and runs the classifier again before calculating emergency risk and recommending hospitals.

## Limitations And Next Improvements

- The current dataset is intentionally balanced by suspected disease in the latest processed CSV, which helps model training but may differ from real-world symptom frequency.
- Evaluation uses a held-out split from the same source distribution. A future improvement is to collect a separate human-labeled validation set.
- Transformer fine-tuning is documented separately as a future path, but the current deployed system uses lightweight TF-IDF models for stability and fast inference.
