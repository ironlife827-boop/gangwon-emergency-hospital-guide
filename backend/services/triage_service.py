from schemas.triage import (
    TriageQuestion,
    TriageAnalyzeRequest,
    TriageAnalyzeResponse,
    RecommendedHospital,
)


def generate_mock_questions(symptom: str) -> list[TriageQuestion]:
    """
    OpenAI API 연결 전 임시 문진 질문 생성 함수.
    나중에는 symptom을 OpenAI에 전달하고,
    동일한 JSON 구조로 질문을 받아오면 된다.
    """

    return [
        TriageQuestion(
            id="q1",
            question="증상이 언제부터 시작되었나요?",
            options=["방금 전", "1시간 이내", "오늘 중", "며칠 전부터"],
        ),
        TriageQuestion(
            id="q2",
            question="현재 증상의 정도는 어떤가요?",
            options=["가벼움", "참을 수 있음", "심함", "매우 심함"],
        ),
        TriageQuestion(
            id="q3",
            question="동반 증상이 있나요?",
            options=["없음", "어지러움", "호흡곤란", "의식 저하"],
        ),
        TriageQuestion(
            id="q4",
            question="현재 혼자 이동할 수 있나요?",
            options=["가능함", "조금 어려움", "거의 불가능", "도움이 필요함"],
        ),
    ]


def analyze_mock_triage(payload: TriageAnalyzeRequest) -> TriageAnalyzeResponse:
    """
    모델 연결 전 임시 분석 결과.
    이후 다음 항목으로 교체한다.

    1. 답변을 피처로 변환
    2. severity_model.pkl 예측
    3. hospital_master.csv 필터링
    4. 실시간 병상 API 확인
    5. eta_model.pkl 예측
    6. 추천 점수 계산
    """

    high_risk_words = ["호흡곤란", "의식 저하", "매우 심함", "도움이 필요함"]
    joined_answers = " ".join(
        [answer.answer + " " + (answer.custom_answer or "") for answer in payload.answers]
    )

    risk_score = 85 if any(word in joined_answers for word in high_risk_words) else 55

    severity_level = 2 if risk_score >= 80 else 3
    severity_label = "긴급" if severity_level == 2 else "주의"

    return TriageAnalyzeResponse(
        severity_level=severity_level,
        severity_label=severity_label,
        risk_score=risk_score,
        required_resource_code="ER_GENERAL",
        summary="입력된 증상과 문진 답변을 기준으로 의료기관 방문이 권장됩니다.",
        hospitals=[
            RecommendedHospital(
                rank=1,
                hospital_name="강원대학교병원",
                eta_min=14,
                available_beds=3,
                recommendation_score=92,
                reason="응급실 병상 여유와 예상 이동시간을 종합했을 때 가장 적합합니다.",
            ),
            RecommendedHospital(
                rank=2,
                hospital_name="한림대학교춘천성심병원",
                eta_min=18,
                available_beds=2,
                recommendation_score=87,
                reason="거리와 병상 상태가 양호하여 차선 추천 병원입니다.",
            ),
            RecommendedHospital(
                rank=3,
                hospital_name="강릉아산병원",
                eta_min=31,
                available_beds=5,
                recommendation_score=81,
                reason="병상 여유는 있으나 예상 이동시간이 상대적으로 깁니다.",
            ),
        ],
    )
