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
    사용자 자연어 증상 입력을 네이버 지식인 실제 사례 데이터와 비교하여
    증상군, 진료과, 의심질환을 추론하고 관련 문진 질문을 반환한다.
    """
    return create_data_driven_questions(payload.symptom)


@router.post("/analyze", response_model=TriageAnalyzeResponse)
def analyze_triage(payload: TriageAnalyzeRequest):
    """
    문진 답변, 실제 사례 유사도, triage_rule_dataset, severity_model,
    hospital_master, eta_model을 결합하여 응급도와 추천 병원을 산출한다.
    """
    return analyze_data_driven_triage(payload)
