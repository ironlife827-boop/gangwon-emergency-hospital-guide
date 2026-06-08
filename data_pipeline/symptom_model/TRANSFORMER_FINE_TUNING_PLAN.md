# GPU 기반 Transformer 파인튜닝 확장 방향

현재 서비스 배포용 모델은 `TF-IDF + LogisticRegression` 기반 `symptom_classifier.pkl`이다.

GPU가 있는 로컬 PC에서는 이후 아래 방향으로 확장 가능하다.

## 추천 모델

- `klue/roberta-base`
- `monologg/koelectra-base-v3-discriminator`
- `beomi/KcELECTRA-base`

## 목표

입력:

```text
가슴이 답답하고 숨이 차요
```

출력:

```json
{
  "symptom_group": "cardio",
  "department": "심장내과",
  "suspected_disease": "급성 심근경색"
}
```

## 왜 바로 Transformer를 배포하지 않는가?

Render 무료 서버에서는 PyTorch/Transformers 모델 로딩이 무겁고,
배포 안정성이 낮다.

따라서 프로젝트 제출용 서비스는 경량 분류 모델을 사용하고,
발표/보고서에서는 GPU 기반 파인튜닝 확장 가능성을 제시하는 것이 안전하다.

## 발표 표현

"OpenAI API를 호출하지 않고, 자체 구축한 네이버 지식인 증상 사례 데이터셋을 기반으로
한국어 자연어 증상 분류 모델을 학습하였다. 배포 환경에서는 경량 TF-IDF 분류기를 사용하고,
로컬 GPU 환경에서는 KoELECTRA/KLUE-RoBERTa 기반 파인튜닝으로 확장 가능하도록 설계하였다."
