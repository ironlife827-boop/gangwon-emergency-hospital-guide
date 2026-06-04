from pydantic import BaseModel, Field


class TriageQuestion(BaseModel):
    id: str
    question: str
    options: list[str]
    allow_custom: bool = True


class TriageQuestionRequest(BaseModel):
    symptom: str = Field(..., min_length=1)


class TriageQuestionResponse(BaseModel):
    symptom: str
    questions: list[TriageQuestion]


class TriageAnswer(BaseModel):
    question_id: str
    question: str
    answer: str
    custom_answer: str | None = None


class TriageAnalyzeRequest(BaseModel):
    symptom: str
    answers: list[TriageAnswer]


class RecommendedHospital(BaseModel):
    rank: int
    hospital_name: str
    eta_min: int
    available_beds: int
    recommendation_score: int
    reason: str


class TriageAnalyzeResponse(BaseModel):
    severity_level: int
    severity_label: str
    risk_score: int
    required_resource_code: str
    summary: str
    hospitals: list[RecommendedHospital]
