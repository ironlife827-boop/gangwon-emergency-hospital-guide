from pydantic import BaseModel, Field


class TriageQuestion(BaseModel):
    id: str
    question: str
    options: list[str]
    allow_custom: bool = False


class SimilarCase(BaseModel):
    case_id: int
    cleaned_text: str
    symptom_group: str
    department: str
    suspected_disease: str
    severity_level: int
    similarity: float
    source_url: str | None = None


class AnalysisEvidence(BaseModel):
    method: str
    model_used: bool
    keyword_rule_used: bool
    similarity_top_score: float
    explanation: str


class TriageQuestionRequest(BaseModel):
    symptom: str = Field(..., min_length=1)
    user_lat: float | None = None
    user_lon: float | None = None


class TriageQuestionResponse(BaseModel):
    symptom: str
    symptom_group: str
    department: str
    suspected_disease: str
    need_followup: bool
    questions: list[TriageQuestion]
    similar_cases: list[SimilarCase] = []
    evidence: AnalysisEvidence


class TriageAnswer(BaseModel):
    question_id: str
    question: str
    answer: str
    custom_answer: str | None = None


class TriageAnalyzeRequest(BaseModel):
    symptom: str
    answers: list[TriageAnswer]
    user_lat: float | None = None
    user_lon: float | None = None


class RecommendedHospital(BaseModel):
    rank: int
    hospital_name: str
    eta_min: int
    available_beds: int
    recommendation_score: int
    reason: str
    department: str | None = None
    address: str | None = None
    phone: str | None = None
    distance_km: float | None = None
    is_emergency: int | None = None


class TriageAnalyzeResponse(BaseModel):
    severity_level: int
    severity_label: str
    risk_score: int
    required_resource_code: str
    symptom_group: str
    department: str
    suspected_disease: str
    summary: str
    evidence: AnalysisEvidence
    similar_cases: list[SimilarCase] = []
    hospitals: list[RecommendedHospital]
