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
  source_url?: string | null;
};

type AnalysisEvidence = {
  method: string;
  model_used: boolean;
  keyword_rule_used: boolean;
  similarity_top_score: number;
  explanation: string;
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
  evidence: AnalysisEvidence;
};

type TriageResult = {
  final_symptom_summary?: string;
  severity_level: number;
  severity_label: string;
  risk_score: number;
  required_resource_code: string;
  symptom_group: string;
  department: string;
  suspected_disease: string;
  summary: string;
  evidence: AnalysisEvidence;
  similar_cases: SimilarCase[];
  hospitals: RecommendedHospital[];
};

const API_BASE_URL = "https://gangwon-emergency-api.onrender.com";

const symptomGroupLabel: Record<string, string> = {
  cardio: "심혈관계",
  neuro: "신경계",
  respiratory: "호흡기계",
  abdominal: "복부/소화기계",
  trauma: "외상",
  toxic: "중독",
  poisoning: "중독",
  allergy: "알레르기",
  bleeding: "출혈",
  eye: "안과",
  foreign_body: "이물질",
  pediatric: "소아",
  obgy: "산부인과",
  psychiatric: "정신건강",
  urology: "비뇨기계",
  etc_emerg: "기타 응급",
  unknown: "기타",
};

const severityGuide: Record<
  number,
  {
    icon: string;
    title: string;
    action: string;
    description: string;
    borderClass: string;
    textClass: string;
    bgClass: string;
  }
> = {
  1: {
    icon: "🚨",
    title: "매우 긴급",
    action: "지금 즉시 119 또는 응급실 방문이 필요합니다.",
    description: "생명에 위험할 수 있는 단계입니다. 지체하지 말고 응급 진료를 받으세요.",
    borderClass: "border-red-500/70",
    textClass: "text-red-200",
    bgClass: "bg-red-500/15",
  },
  2: {
    icon: "⚠️",
    title: "긴급",
    action: "가능한 빨리 응급 진료를 받는 것이 좋습니다.",
    description: "빠른 평가와 처치가 필요한 단계입니다. 증상이 악화되면 즉시 119에 연락하세요.",
    borderClass: "border-orange-400/70",
    textClass: "text-orange-100",
    bgClass: "bg-orange-500/15",
  },
  3: {
    icon: "🟡",
    title: "주의",
    action: "당일 또는 빠른 시간 내 병원 진료를 권장합니다.",
    description: "중등도 위험 가능성이 있습니다. 통증이나 증상이 심해지면 응급실 방문을 고려하세요.",
    borderClass: "border-yellow-400/70",
    textClass: "text-yellow-100",
    bgClass: "bg-yellow-500/15",
  },
  4: {
    icon: "🟢",
    title: "낮음",
    action: "일반 진료 또는 외래 방문을 권장합니다.",
    description: "비교적 안정적인 단계입니다. 새 증상이 생기거나 악화되면 다시 평가하세요.",
    borderClass: "border-emerald-400/70",
    textClass: "text-emerald-100",
    bgClass: "bg-emerald-500/15",
  },
  5: {
    icon: "🔵",
    title: "비응급",
    action: "여유 있는 시간에 일반 진료를 받아도 되는 단계입니다.",
    description: "응급 가능성은 낮지만 증상이 지속되면 의료기관 상담을 받으세요.",
    borderClass: "border-sky-400/70",
    textClass: "text-sky-100",
    bgClass: "bg-sky-500/15",
  },
};

const groupLabel = (group?: string | null) => {
  if (!group) return "-";
  return symptomGroupLabel[group] ?? group;
};

const getSeverityGuide = (level: number) => severityGuide[level] ?? severityGuide[3];

const normalizeRiskScore = (score: number) => Math.max(0, Math.min(10, Math.round(score)));

const shortDepartment = (value?: string | null) => {
  if (!value) return "-";
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3)
    .join(", ");
};

const methodLabel = (method: string) => {
  if (method === "keyword_rule") return "응급 키워드 안전장치";
  if (method === "trained_classifier") return "네이버 증상 학습 모델";
  return "유사 사례 검색";
};

const severityText = (level: number) => {
  if (level >= 5) return "매우 위험";
  if (level === 4) return "위험";
  if (level === 3) return "주의";
  if (level === 2) return "낮음";
  return "경미";
};

export default function Home() {
  const [symptom, setSymptom] = useState("");
  const [userLat, setUserLat] = useState("");
  const [userLon, setUserLon] = useState("");
  const [questionResponse, setQuestionResponse] = useState<QuestionResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<TriageResult | null>(null);

  const [questionLoading, setQuestionLoading] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const numericLat = userLat.trim() ? Number(userLat) : null;
  const numericLon = userLon.trim() ? Number(userLon) : null;

  const resetConsultation = () => {
    setQuestionResponse(null);
    setAnswers({});
    setResult(null);
    setErrorMessage("");
  };

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage("현재 브라우저에서 위치 권한을 지원하지 않습니다.");
      return;
    }

    setLocationLoading(true);
    setErrorMessage("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLat(position.coords.latitude.toFixed(6));
        setUserLon(position.coords.longitude.toFixed(6));
        setLocationLoading(false);
      },
      () => {
        setErrorMessage("위치 정보를 가져오지 못했습니다. 위도와 경도를 직접 입력해주세요.");
        setLocationLoading(false);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symptom,
          user_lat: numericLat,
          user_lon: numericLon,
        }),
      });

      if (!response.ok) throw new Error("문진 질문을 불러오지 못했습니다.");

      const data = await response.json();
      setQuestionResponse(data);
    } catch {
      setErrorMessage("백엔드 서버와 연결되지 않았습니다. Render 배포 상태를 확인해주세요.");
    } finally {
      setQuestionLoading(false);
    }
  };

  const handleSelect = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
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
    (questionResponse.questions.length === 0 ||
      questionResponse.questions.every((item) => !!answers[item.id]));

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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symptom,
          answers: buildPayloadAnswers(),
          user_lat: numericLat,
          user_lon: numericLon,
        }),
      });

      if (!response.ok) throw new Error("응급도 분석에 실패했습니다.");

      const data = await response.json();
      setResult(data);
    } catch {
      setErrorMessage("분석 요청에 실패했습니다. 백엔드 로그를 확인해주세요.");
    } finally {
      setAnalyzeLoading(false);
    }
  };

  const topHospital = result?.hospitals?.[0];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto max-w-5xl px-5 py-8 md:py-10">
        <header className="mb-8 text-center">
          <p className="mb-3 text-sm font-semibold text-cyan-400">Gangwon Emergency Hospital Guide</p>
          <h1 className="text-3xl font-bold leading-tight md:text-5xl">
            강원도 맞춤형 응급 및
            <br />
            상시 병원 안내 시스템
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm text-slate-300 md:text-base">
            증상을 입력하면 필요한 추가 질문만 확인한 뒤, 응급도와 가까운 병원을 안내합니다.
          </p>
        </header>

        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-2xl md:p-7">
          <div className="mb-7">
            <h2 className="mb-4 text-2xl font-bold">증상 입력</h2>

            <textarea
              value={symptom}
              onChange={(event) => {
                setSymptom(event.target.value);
                resetConsultation();
              }}
              className="min-h-28 w-full rounded-2xl border border-slate-700 bg-slate-950 p-4 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
              placeholder="예: 갑자기 왼팔에 힘이 빠지고 말이 어눌해졌어요."
            />

            <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-semibold">사용자 위치</p>
                  <p className="mt-1 text-xs text-slate-500">병원 추천과 예상 이동시간 계산에 사용됩니다.</p>
                </div>

                <button
                  type="button"
                  onClick={handleGetCurrentLocation}
                  disabled={locationLoading}
                  className="rounded-xl border border-cyan-400 px-4 py-2 text-sm font-semibold text-cyan-300 transition hover:bg-cyan-400 hover:text-slate-950 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
                >
                  {locationLoading ? "위치 확인 중..." : "현재 위치 사용"}
                </button>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <input
                  value={userLat}
                  onChange={(event) => setUserLat(event.target.value)}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                  placeholder="위도 예: 37.881315"
                />
                <input
                  value={userLon}
                  onChange={(event) => setUserLon(event.target.value)}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                  placeholder="경도 예: 127.729971"
                />
              </div>
            </div>

            <button
              onClick={handleStartConsultation}
              disabled={!symptom.trim() || questionLoading}
              className="mt-4 rounded-2xl bg-cyan-400 px-6 py-3 font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              {questionLoading ? "필요한 질문 확인 중..." : "문진 시작"}
            </button>

            {errorMessage && (
              <p className="mt-4 rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
                {errorMessage}
              </p>
            )}
          </div>

          {questionResponse && !result && (
            <div className="border-t border-slate-800 pt-7">
              <div className="mb-5 rounded-2xl border border-cyan-400/30 bg-cyan-400/10 p-4">
                <h2 className="text-xl font-bold">추가 확인 질문</h2>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  입력한 증상만으로 부족한 핵심 정보만 확인합니다. 답변 후 최종 응급도와 병원을 한 번에 안내합니다.
                </p>
              </div>

              {questionResponse.questions.length === 0 ? (
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-sm text-slate-300">
                  추가 질문 없이 바로 분석 가능한 상태입니다.
                </div>
              ) : (
                <div className="space-y-4">
                  {questionResponse.questions.map((item, index) => (
                    <div key={item.id} className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
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
              )}

              <button
                onClick={handleAnalyze}
                disabled={!isAllAnswered || analyzeLoading}
                className="mt-6 w-full rounded-2xl bg-white px-6 py-4 font-bold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              >
                {analyzeLoading ? "최종 분석 중..." : "최종 응급도 및 병원 확인"}
              </button>
            </div>
          )}

          {result && (
            <section className="border-t border-slate-800 pt-7">
              {(() => {
                const guide = getSeverityGuide(result.severity_level);
                const riskScore = normalizeRiskScore(result.risk_score);
                const riskPercent = riskScore * 10;

                return (
                  <div className={`rounded-3xl border p-5 md:p-7 ${guide.borderClass} ${guide.bgClass}`}>
                    <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                      <div>
                        <p className="text-sm font-semibold text-slate-300">최종 응급도</p>
                        <div className="mt-3 flex items-center gap-4">
                          <span className="text-5xl" aria-hidden="true">{guide.icon}</span>
                          <div>
                            <p className="text-sm font-bold text-slate-300">
                              {result.severity_level}단계 / 5단계 · 1단계가 가장 위급
                            </p>
                            <h2 className={`mt-1 text-4xl font-extrabold ${guide.textClass}`}>{guide.title}</h2>
                          </div>
                        </div>
                        <p className="mt-5 text-xl font-extrabold text-white">{guide.action}</p>
                        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">{guide.description}</p>
                      </div>

                      <div className="rounded-2xl bg-slate-950/80 p-4 md:min-w-60">
                        <div className="flex items-end justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-400">위험도</p>
                          <p className="text-3xl font-extrabold text-white">
                            {riskScore}<span className="text-base text-slate-400"> / 10</span>
                          </p>
                        </div>
                        <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-yellow-300 to-red-500"
                            style={{ width: `${riskPercent}%` }}
                          />
                        </div>
                        <div className="mt-2 flex justify-between text-[11px] text-slate-500">
                          <span>낮음</span>
                          <span>높음</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {topHospital && (
                <div className="mt-5 rounded-3xl border border-cyan-400/40 bg-cyan-400/10 p-5 md:p-6">
                  <p className="text-sm font-semibold text-cyan-300">가장 먼저 확인할 병원</p>
                  <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div>
                      <h3 className="text-2xl font-extrabold text-white">{topHospital.hospital_name}</h3>
                      <p className="mt-2 text-sm text-slate-300">{topHospital.reason}</p>
                      {topHospital.address && <p className="mt-3 text-xs text-slate-500">{topHospital.address}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm md:min-w-80">
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        <p className="text-slate-500">예상 이동</p>
                        <p className="mt-1 font-bold text-white">{topHospital.eta_min}분</p>
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        <p className="text-slate-500">거리</p>
                        <p className="mt-1 font-bold text-white">{topHospital.distance_km}km</p>
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        <p className="text-slate-500">응급 병상</p>
                        <p className="mt-1 font-bold text-white">{topHospital.available_beds}개</p>
                      </div>
                      <div className="rounded-xl bg-slate-950/70 p-3">
                        <p className="text-slate-500">추천 점수</p>
                        <p className="mt-1 font-bold text-white">{topHospital.recommendation_score}점</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-5 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">의심 질환</p>
                  <p className="mt-1 text-lg font-bold text-cyan-300">{result.suspected_disease}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">추천 진료과</p>
                  <p className="mt-1 text-lg font-bold text-cyan-300">{result.department}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                  <p className="text-xs text-slate-500">증상군</p>
                  <p className="mt-1 text-lg font-bold text-cyan-300">{groupLabel(result.symptom_group)}</p>
                </div>
              </div>

              {(result.final_symptom_summary || result.summary) && (
                <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950 p-5">
                  <h3 className="text-lg font-bold">최종 증상 정리</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-300">
                    {result.final_symptom_summary || result.summary}
                  </p>
                </div>
              )}

              {result.hospitals.length > 1 && (
                <div className="mt-6">
                  <h3 className="mb-3 text-xl font-bold">다른 추천 병원</h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    {result.hospitals.slice(1).map((hospital) => (
                      <article key={`${hospital.rank}-${hospital.hospital_name}`} className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                        <p className="text-xs font-semibold text-cyan-300">추천 {hospital.rank}순위</p>
                        <h4 className="mt-1 font-bold text-white">{hospital.hospital_name}</h4>
                        <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-300">
                          <p>이동 {hospital.eta_min}분</p>
                          <p>거리 {hospital.distance_km}km</p>
                          <p>병상 {hospital.available_beds}개</p>
                          <p>점수 {hospital.recommendation_score}점</p>
                        </div>
                        <p className="mt-3 text-xs text-slate-500">주요 진료과: {shortDepartment(hospital.department)}</p>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              <details className="mt-6 rounded-2xl border border-slate-800 bg-slate-950 p-5">
                <summary className="cursor-pointer text-lg font-bold text-slate-100">
                  분석 근거와 유사 사례 보기
                </summary>

                <div className="mt-5 space-y-5">
                  <div className="rounded-2xl bg-slate-900 p-4">
                    <p className="text-sm font-bold text-white">분석 방식</p>
                    <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
                      <div className="rounded-xl bg-slate-950 p-3">
                        <p className="text-slate-500">모델</p>
                        <p className="mt-1 font-semibold text-cyan-300">{methodLabel(result.evidence.method)}</p>
                      </div>
                      <div className="rounded-xl bg-slate-950 p-3">
                        <p className="text-slate-500">최고 유사도</p>
                        <p className="mt-1 font-semibold text-cyan-300">
                          {(result.evidence.similarity_top_score * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="rounded-xl bg-slate-950 p-3">
                        <p className="text-slate-500">필요 자원</p>
                        <p className="mt-1 font-semibold text-cyan-300">{result.required_resource_code}</p>
                      </div>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-400">{result.evidence.explanation}</p>
                  </div>

                  <div>
                    <p className="mb-3 text-sm font-bold text-white">네이버 지식인 유사 사례</p>
                    <div className="space-y-3">
                      {result.similar_cases.slice(0, 3).map((item) => (
                        <div key={item.case_id} className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300">
                          <p className="font-medium text-slate-100">{item.cleaned_text}</p>
                          <div className="mt-3 flex flex-wrap gap-2 text-xs">
                            <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-cyan-300">{item.department}</span>
                            <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-cyan-300">{item.suspected_disease}</span>
                            <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">
                              유사도 {(item.similarity * 100).toFixed(1)}%
                            </span>
                            <span className="rounded-full bg-red-400/10 px-3 py-1 text-red-300">
                              사례 위험도 {item.severity_level} · {severityText(item.severity_level)}
                            </span>
                          </div>
                          {item.source_url && item.source_url.startsWith("http") && (
                            <a
                              href={item.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-4 inline-flex rounded-xl border border-cyan-400 px-3 py-2 text-xs font-semibold text-cyan-300 transition hover:bg-cyan-400 hover:text-slate-950"
                            >
                              네이버 원문 보기
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </details>
            </section>
          )}
        </section>
      </section>
    </main>
  );
}
