"use client";

import { useState } from "react";

type SimilarCase = {
  case_id: number;
  cleaned_text: string;
  symptom_group: string;
  department: string;
  suspected_disease: string;
  severity_level: number;
  similarity: number;
};

type TriageQuestion = {
  id: string;
  question: string;
  options: string[];
  allow_custom: boolean;
};

type TriageAnswer = {
  question_id: string;
  question: string;
  answer: string;
  custom_answer?: string | null;
};

type RecommendedHospital = {
  rank: number;
  hospital_name: string;
  eta_min: number;
  available_beds: number;
  recommendation_score: number;
  reason: string;
  department?: string | null;
  address?: string | null;
  phone?: string | null;
  distance_km?: number | null;
  is_emergency?: number | null;
};

type QuestionResponse = {
  symptom: string;
  symptom_group: string;
  department: string;
  suspected_disease: string;
  need_followup: boolean;
  questions: TriageQuestion[];
  similar_cases: SimilarCase[];
};

type TriageResult = {
  severity_level: number;
  severity_label: string;
  risk_score: number;
  required_resource_code: string;
  symptom_group: string;
  department: string;
  suspected_disease: string;
  summary: string;
  similar_cases: SimilarCase[];
  hospitals: RecommendedHospital[];
};

const API_BASE_URL = "https://gangwon-emergency-api.onrender.com";

export default function Home() {
  const [symptom, setSymptom] = useState("");
  const [questionResponse, setQuestionResponse] = useState<QuestionResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<TriageResult | null>(null);

  const [questionLoading, setQuestionLoading] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const resetConsultation = () => {
    setQuestionResponse(null);
    setAnswers({});
    setResult(null);
    setErrorMessage("");
  };

  const handleStartConsultation = async () => {
    if (!symptom.trim()) return;

    setQuestionLoading(true);
    setErrorMessage("");
    setQuestionResponse(null);
    setAnswers({});
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/triage/questions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ symptom }),
      });

      if (!response.ok) {
        throw new Error("문진 질문을 불러오지 못했습니다.");
      }

      const data = await response.json();
      setQuestionResponse(data);
    } catch {
      setErrorMessage("백엔드 서버와 연결되지 않았습니다. Render 배포 상태를 확인해주세요.");
    } finally {
      setQuestionLoading(false);
    }
  };

  const handleSelect = (questionId: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  const buildPayloadAnswers = (): TriageAnswer[] => {
    if (!questionResponse) return [];

    return questionResponse.questions.map((item) => ({
      question_id: item.id,
      question: item.question,
      answer: answers[item.id],
      custom_answer: null,
    }));
  };

  const isAllAnswered =
    !!questionResponse &&
    questionResponse.questions.length > 0 &&
    questionResponse.questions.every((item) => !!answers[item.id]);

  const handleAnalyze = async () => {
    if (!isAllAnswered) {
      setErrorMessage("모든 문진 질문에 답변해주세요.");
      return;
    }

    setAnalyzeLoading(true);
    setErrorMessage("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/triage/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symptom,
          answers: buildPayloadAnswers(),
        }),
      });

      if (!response.ok) {
        throw new Error("응급도 분석에 실패했습니다.");
      }

      const data = await response.json();
      setResult(data);
    } catch {
      setErrorMessage("분석 요청에 실패했습니다. 백엔드 로그를 확인해주세요.");
    } finally {
      setAnalyzeLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto max-w-6xl px-6 py-10">
        <header className="mb-10 text-center">
          <p className="mb-3 text-sm font-semibold text-cyan-400">
            Gangwon Emergency Hospital Guide
          </p>

          <h1 className="text-4xl font-bold leading-tight md:text-6xl">
            강원도 맞춤형 응급 및
            <br />
            상시 병원 안내 시스템
          </h1>

          <p className="mx-auto mt-5 max-w-3xl text-slate-300 md:text-lg">
            사용자의 자연어 증상을 실제 사례 데이터, 문진 규칙, 응급도 모델,
            병원·ETA 데이터를 결합해 분석합니다.
          </p>
        </header>

        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl md:p-8">
          <div className="mb-8">
            <h2 className="mb-4 text-2xl font-bold">증상 입력</h2>

            <textarea
              value={symptom}
              onChange={(event) => {
                setSymptom(event.target.value);
                resetConsultation();
              }}
              className="min-h-32 w-full rounded-2xl border border-slate-700 bg-slate-950 p-4 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
              placeholder="예: 갑자기 가슴이 답답하고 숨쉬기가 어려워요."
            />

            <button
              onClick={handleStartConsultation}
              disabled={!symptom.trim() || questionLoading}
              className="mt-4 rounded-2xl bg-cyan-400 px-6 py-3 font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {questionLoading ? "증상 분석 중..." : "증상 분석 및 문진 시작"}
            </button>

            {errorMessage && (
              <p className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
                {errorMessage}
              </p>
            )}
          </div>

          {questionResponse && (
            <div className="border-t border-slate-800 pt-8">
              <div className="mb-6 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">증상군</p>
                  <p className="mt-1 font-bold text-cyan-300">
                    {questionResponse.symptom_group}
                  </p>
                </div>

                <div className="rounded-2xl bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">추천 진료과</p>
                  <p className="mt-1 font-bold text-cyan-300">
                    {questionResponse.department}
                  </p>
                </div>

                <div className="rounded-2xl bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">의심 질환</p>
                  <p className="mt-1 font-bold text-cyan-300">
                    {questionResponse.suspected_disease}
                  </p>
                </div>
              </div>

              <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-950 p-5">
                <h2 className="text-xl font-bold">유사 실제 사례</h2>
                <div className="mt-4 space-y-3">
                  {questionResponse.similar_cases.slice(0, 3).map((item) => (
                    <div
                      key={item.case_id}
                      className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300"
                    >
                      <p>{item.cleaned_text}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        {item.department} · {item.suspected_disease} · 유사도{" "}
                        {(item.similarity * 100).toFixed(1)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-6">
                <h2 className="text-2xl font-bold">추가 문진</h2>
                <p className="mt-2 text-sm text-slate-400">
                  분석에 필요한 핵심 질문만 선택적으로 제시합니다.
                </p>
              </div>

              <div className="space-y-6">
                {questionResponse.questions.map((item, index) => (
                  <div
                    key={item.id}
                    className="rounded-2xl border border-slate-800 bg-slate-950 p-5"
                  >
                    <p className="mb-4 font-semibold">
                      Q{index + 1}. {item.question}
                    </p>

                    <div className="grid gap-3 md:grid-cols-3">
                      {item.options.map((option) => (
                        <button
                          key={option}
                          onClick={() => handleSelect(item.id, option)}
                          className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
                            answers[item.id] === option
                              ? "border-cyan-400 bg-cyan-400 text-slate-950"
                              : "border-slate-700 bg-slate-900 text-slate-300 hover:border-cyan-400"
                          }`}
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!isAllAnswered || analyzeLoading}
                className="mt-8 w-full rounded-2xl bg-white px-6 py-4 font-bold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              >
                {analyzeLoading ? "응급도 및 병원 분석 중..." : "응급도 분석 및 병원 추천"}
              </button>

              {result && (
                <section className="mt-8 space-y-6 border-t border-slate-800 pt-8">
                  <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-5">
                    <p className="text-sm font-semibold text-red-300">
                      응급도 판단 결과
                    </p>

                    <h3 className="mt-2 text-3xl font-bold text-red-200">
                      응급도 {result.severity_level}단계 — {result.severity_label}
                    </h3>

                    <p className="mt-3 text-sm text-slate-300">
                      {result.summary}
                    </p>

                    <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        위험 점수: {result.risk_score}점
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        필요 자원: {result.required_resource_code}
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        진료과: {result.department}
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        증상군: {result.symptom_group}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="mb-4 text-2xl font-bold">추천 병원</h3>

                    <div className="grid gap-4 md:grid-cols-3">
                      {result.hospitals.map((hospital) => (
                        <article
                          key={`${hospital.rank}-${hospital.hospital_name}`}
                          className="rounded-2xl border border-slate-800 bg-slate-950 p-5"
                        >
                          <p className="mb-2 text-sm font-semibold text-cyan-300">
                            추천 {hospital.rank}순위
                          </p>

                          <h4 className="text-lg font-bold">
                            {hospital.hospital_name}
                          </h4>

                          <div className="mt-4 space-y-2 text-sm text-slate-300">
                            <p>진료과: {hospital.department}</p>
                            <p>예상 이동시간: {hospital.eta_min}분</p>
                            <p>거리: {hospital.distance_km}km</p>
                            <p>응급 병상: {hospital.available_beds}개</p>
                            <p>추천 점수: {hospital.recommendation_score}점</p>
                          </div>

                          <p className="mt-4 text-sm text-slate-400">
                            {hospital.reason}
                          </p>

                          {hospital.address && (
                            <p className="mt-3 text-xs text-slate-500">
                              {hospital.address}
                            </p>
                          )}
                        </article>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                    <h3 className="mb-4 text-2xl font-bold">지도 시각화</h3>

                    <div className="flex h-72 items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-900 text-sm text-slate-500">
                      지도 API 연동 예정 영역
                    </div>
                  </div>
                </section>
              )}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
