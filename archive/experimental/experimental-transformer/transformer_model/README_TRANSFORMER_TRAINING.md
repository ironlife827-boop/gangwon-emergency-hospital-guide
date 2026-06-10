# Local Transformer / LLM-Style Symptom Model Training

## 목적

OpenAI API를 사용하지 않고, 자체 수집한 네이버 지식인 증상 데이터로
한국어 Transformer 계열 모델을 파인튜닝한다.

이 모델은 사용자 자연어 증상 입력을 기반으로 다음을 예측한다.

- symptom_group
- department
- suspected_disease

## 핵심 구조

```text
사용자 자연어 증상
↓
자체 학습 한국어 Transformer 모델
↓
증상군 / 진료과 / 의심질환 예측
↓
triage_rule_dataset 기반 부족 정보 질문 선택
↓
severity_model.pkl 응급도 판단
↓
hospital_master.csv + eta_model.pkl 병원 추천
```

## 설치

프로젝트 루트에서 실행:

```powershell
pip install -r data_pipeline\transformer_model\requirements_transformer.txt
```

CUDA GPU가 있으면 PyTorch CUDA 버전을 별도로 설치하는 것이 좋다.

## 학습

전체 3개 타깃 학습:

```powershell
python data_pipeline\transformer_model\train_transformer_symptom_classifier.py --epochs 5 --batch-size 8
```

특정 타깃만 학습:

```powershell
python data_pipeline\transformer_model\train_transformer_symptom_classifier.py --target symptom_group
python data_pipeline\transformer_model\train_transformer_symptom_classifier.py --target department
python data_pipeline\transformer_model\train_transformer_symptom_classifier.py --target suspected_disease
```

## 모델 저장 위치

```text
models/transformer_symptom_classifier/
├─ symptom_group/
├─ department/
└─ suspected_disease/
```

## 예측 테스트

```powershell
python data_pipeline\transformer_model\predict_transformer_symptom.py --text "가슴이 답답하고 숨이 차요"
```

## 주의

Render 무료 서버에 Transformer 모델을 바로 올리는 것은 무겁다.
현재 배포용 FastAPI는 `symptom_classifier.pkl`을 사용하고,
로컬 GPU 학습 결과는 보고서/발표 및 고도화 버전으로 활용하는 것을 권장한다.

## 발표 표현

"OpenAI API를 호출하지 않고, 자체 수집한 네이버 지식인 증상 사례 데이터셋을 기반으로
한국어 Transformer 모델을 파인튜닝하여 사용자 자연어 증상 입력을 증상군, 진료과,
의심질환으로 구조화하였다."
