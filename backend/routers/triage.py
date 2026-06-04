from fastapi import APIRouter
from schemas.triage import (
    TriageQuestionRequest,
    TriageQuestionResponse,
    TriageAnalyzeRequest,
    TriageAnalyzeResponse,
)
from services.triage_service import generate_mock_questions, analyze_mock_triage

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("/questions", response_model=TriageQuestionResponse)
def create_triage_questions(payload: TriageQuestionRequest):
    """
    현재 단계에서는 OpenAI 연동 전 mock 질문을 반환한다.
    이후 이 함수 내부를 OpenAI API 기반 질문 생성 로직으로 교체한다.
    """
    questions = generate_mock_questions(payload.symptom)

    return TriageQuestionResponse(
        symptom=payload.symptom,
        questions=questions,
    )


@router.post("/analyze", response_model=TriageAnalyzeResponse)
def analyze_triage(payload: TriageAnalyzeRequest):
    """
    현재 단계에서는 임시 응급도와 병원 추천 결과를 반환한다.
    이후 severity_model.pkl, eta_model.pkl, hospital_master.csv와 연결한다.
    """
    return analyze_mock_triage(payload)
