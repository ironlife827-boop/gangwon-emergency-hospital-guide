"use client";

import { useState } from "react";

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
};

type TriageResult = {
  severity_level: number;
  severity_label: string;
  risk_score: number;
  required_resource_code: string;
  summary: string;
  hospitals: RecommendedHospital[];
};

const API_BASE_URL = "https://gangwon-api.onrender.com";

export default function Home() {
  const [symptom, setSymptom] = useState("");
  const [started, setStarted] = useState(false);
  const [questions, setQuestions] = useState<TriageQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [customAnswers, setCustomAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<TriageResult | null>(null);

  const [questionLoading, setQuestionLoading] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const resetConsultation = () => {
    setStarted(false);
    setQuestions([]);
    setAnswers({});
    setCustomAnswers({});
    setResult(null);
    setErrorMessage("");
  };

  const handleStartConsultation = async () => {
    if (!symptom.trim()) return;

    setQuestionLoading(true);
    setErrorMessage("");
    setStarted(false);
    setQuestions([]);
    setAnswers({});
    setCustomAnswers({});
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/triage/questions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symptom,
        }),
      });

      if (!response.ok) {
        throw new Error("문진 질문을 불러오지 못했습니다.");
      }

      const data = await response.json();

      setQuestions(data.questions ?? []);
      setStarted(true);
    } catch {
      setErrorMessage(
        "백엔드 서버와 연결되지 않았습니다. FastAPI 서버가 실행 중인지 확인해주세요."
      );
    } finally {
      setQuestionLoading(false);
    }
  };

  const handleSelect = (questionId: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));

    if (value !== "기타") {
      setCustomAnswers((prev) => {
        const next = { ...prev };
        delete next[questionId];
        return next;
      });
    }
  };

  const buildPayloadAnswers = (): TriageAnswer[] => {
    return questions.map((item) => ({
      question_id: item.id,
      question: item.question,
      answer: answers[item.id],
      custom_answer:
        answers[item.id] === "기타" ? customAnswers[item.id] ?? "" : null,
    }));
  };

  const isAllAnswered =
    questions.length > 0 &&
    questions.every((item) => {
      if (!answers[item.id]) return false;
      if (answers[item.id] === "기타" && !customAnswers[item.id]?.trim()) {
        return false;
      }
      return true;
    });

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
      setErrorMessage(
        "분석 요청에 실패했습니다. FastAPI 서버가 실행 중인지 확인해주세요."
      );
    } finally {
      setAnalyzeLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto max-w-5xl px-6 py-10">
        <header className="mb-10 text-center">
          <p className="mb-3 text-sm font-semibold text-cyan-400">
            Gangwon Emergency Hospital Guide
          </p>

          <h1 className="text-4xl font-bold leading-tight md:text-6xl">
            강원도 맞춤형 응급 및
            <br />
            상시 병원 안내 시스템
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-slate-300 md:text-lg">
            증상을 입력하면 AI 문진을 통해 현재 상황에 맞는 응급도와 병원을
            추천합니다.
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
              {questionLoading ? "문진 질문 생성 중..." : "AI 문진 시작"}
            </button>

            {errorMessage && (
              <p className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
                {errorMessage}
              </p>
            )}
          </div>

          {started && (
            <div className="border-t border-slate-800 pt-8">
              <div className="mb-6">
                <h2 className="text-2xl font-bold">AI 추가 문진</h2>
                <p className="mt-2 text-sm text-slate-400">
                  입력한 증상을 바탕으로 필요한 질문에 답변해주세요.
                </p>
              </div>

              <div className="space-y-6">
                {questions.map((item, index) => (
                  <div
                    key={item.id}
                    className="rounded-2xl border border-slate-800 bg-slate-950 p-5"
                  >
                    <p className="mb-4 font-semibold">
                      Q{index + 1}. {item.question}
                    </p>

                    <div className="grid gap-3 md:grid-cols-2">
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

                      {item.allow_custom && (
                        <button
                          onClick={() => handleSelect(item.id, "기타")}
                          className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
                            answers[item.id] === "기타"
                              ? "border-cyan-400 bg-cyan-400 text-slate-950"
                              : "border-slate-700 bg-slate-900 text-slate-300 hover:border-cyan-400"
                          }`}
                        >
                          기타 직접 입력
                        </button>
                      )}
                    </div>

                    {answers[item.id] === "기타" && (
                      <input
                        value={customAnswers[item.id] ?? ""}
                        onChange={(event) =>
                          setCustomAnswers((prev) => ({
                            ...prev,
                            [item.id]: event.target.value,
                          }))
                        }
                        className="mt-4 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                        placeholder="직접 답변을 입력하세요."
                      />
                    )}
                  </div>
                ))}
              </div>

              <button
                onClick={handleAnalyze}
                disabled={!isAllAnswered || analyzeLoading}
                className="mt-8 w-full rounded-2xl bg-white px-6 py-4 font-bold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              >
                {analyzeLoading
                  ? "응급도 분석 중..."
                  : "응급도 분석 및 병원 추천"}
              </button>

              {result && (
                <section className="mt-8 space-y-6 border-t border-slate-800 pt-8">
                  <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-5">
                    <p className="text-sm font-semibold text-red-300">
                      응급도 판단 결과
                    </p>

                    <h3 className="mt-2 text-3xl font-bold text-red-200">
                      응급도 {result.severity_level}단계 —{" "}
                      {result.severity_label}
                    </h3>

                    <p className="mt-3 text-sm text-slate-300">
                      {result.summary}
                    </p>

                    <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        위험 점수: {result.risk_score}점
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        필요 자원: {result.required_resource_code}
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        추천 기준: 병상 + ETA + 적합도
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="mb-4 text-2xl font-bold">추천 병원</h3>

                    <div className="grid gap-4 md:grid-cols-3">
                      {result.hospitals.map((hospital) => (
                        <article
                          key={hospital.hospital_name}
                          className="rounded-2xl border border-slate-800 bg-slate-950 p-5"
                        >
                          <p className="mb-2 text-sm font-semibold text-cyan-300">
                            추천 {hospital.rank}순위
                          </p>

                          <h4 className="text-lg font-bold">
                            {hospital.hospital_name}
                          </h4>

                          <div className="mt-4 space-y-2 text-sm text-slate-300">
                            <p>예상 이동시간: {hospital.eta_min}분</p>
                            <p>응급 병상: {hospital.available_beds}개</p>
                            <p>추천 점수: {hospital.recommendation_score}점</p>
                          </div>

                          <p className="mt-4 text-sm text-slate-400">
                            {hospital.reason}
                          </p>
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
