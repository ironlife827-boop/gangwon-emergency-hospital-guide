from fastapi import APIRouter

from schemas.triage import (
    TriageAnalyzeRequest,
    TriageAnalyzeResponse,
    TriageQuestionRequest,
    TriageQuestionResponse,
)
from services.triage_service import (
    analyze_data_driven_triage,
    create_data_driven_questions,
)

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("/questions", response_model=TriageQuestionResponse)
def create_triage_questions(payload: TriageQuestionRequest):
    """
    자연어 증상을 symptom_classifier.pkl로 예측한 뒤 질환별 문진 질문을 반환한다.
    """
    return create_data_driven_questions(payload.symptom)


@router.post("/analyze", response_model=TriageAnalyzeResponse)
def analyze_triage(payload: TriageAnalyzeRequest):
    """
    최초 증상과 문진 답변을 합쳐 최종 질환, 응급도, 추천 병원을 산출한다.
    """
    return analyze_data_driven_triage(payload)
