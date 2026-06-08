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

const methodLabel = (method: string) => {
  if (method === "keyword_rule") return "응급 키워드 우선 룰";
  if (method === "trained_classifier") return "자체 학습 증상 분류 모델";
  return "유사 사례 검색";
};

const groupLabel = (group?: string | null) => {
  if (!group) return "-";
  return symptomGroupLabel[group] ?? group;
};

const shortDepartment = (value?: string | null) => {
  if (!value) return "-";
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3)
    .join(", ");
};

const severityText = (level: number) => {
  if (level >= 5) return "매우 위험";
  if (level === 4) return "위험";
  if (level === 3) return "주의";
  if (level === 2) return "낮음";
  return "경미";
};

const severityGuide: Record<
  number,
  {
    icon: string;
    title: string;
    action: string;
    description: string;
    cardClass: string;
    badgeClass: string;
  }
> = {
  1: {
    icon: "🚨",
    title: "매우 긴급",
    action: "즉시 응급실 방문 또는 119 신고가 필요합니다.",
    description: "생명에 위험할 수 있는 상태입니다. 지체하지 말고 가장 가까운 응급실로 이동하세요.",
    cardClass: "border-red-500/70 bg-red-500/15",
    badgeClass: "bg-red-400 text-slate-950",
  },
  2: {
    icon: "⚠️",
    title: "긴급",
    action: "가능한 빨리 응급 진료를 받는 것이 좋습니다.",
    description: "빠른 평가와 처치가 필요한 단계입니다. 증상이 악화되면 즉시 119에 연락하세요.",
    cardClass: "border-orange-400/70 bg-orange-500/15",
    badgeClass: "bg-orange-300 text-slate-950",
  },
  3: {
    icon: "🟡",
    title: "주의",
    action: "당일 또는 빠른 시간 내 병원 진료를 권장합니다.",
    description: "현재 증상만으로는 중등도 위험 가능성이 있습니다. 변화가 있으면 응급실 방문을 고려하세요.",
    cardClass: "border-yellow-400/70 bg-yellow-500/15",
    badgeClass: "bg-yellow-300 text-slate-950",
  },
  4: {
    icon: "🟢",
    title: "낮음",
    action: "일반 진료 또는 외래 방문을 권장합니다.",
    description: "비교적 안정적인 단계입니다. 다만 통증이 심해지거나 새 증상이 생기면 재평가가 필요합니다.",
    cardClass: "border-emerald-400/70 bg-emerald-500/15",
    badgeClass: "bg-emerald-300 text-slate-950",
  },
  5: {
    icon: "🔵",
    title: "비응급",
    action: "여유 있는 시간에 일반 진료를 받아도 되는 단계입니다.",
    description: "응급 가능성은 낮지만 증상이 지속되거나 악화되면 병원 상담을 받으세요.",
    cardClass: "border-sky-400/70 bg-sky-500/15",
    badgeClass: "bg-sky-300 text-slate-950",
  },
};

const getSeverityGuide = (level: number) => {
  return severityGuide[level] ?? severityGuide[3];
};

const normalizeRiskScore = (score: number) => {
  return Math.max(0, Math.min(10, Math.round(score)));
};

export default function Home() {
  const [symptom, setSymptom] = useState("");
  const [userLat, setUserLat] = useState("");
  const [userLon, setUserLon] = useState("");
  const [questionResponse, setQuestionResponse] =
    useState<QuestionResponse | null>(null);
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
        setErrorMessage(
          "위치 정보를 가져오지 못했습니다. 위도와 경도를 직접 입력해주세요."
        );
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
      setErrorMessage(
        "백엔드 서버와 연결되지 않았습니다. Render 배포 상태를 확인해주세요."
      );
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
            자체 수집한 증상 사례 데이터, 증상 분류 모델, 문진 규칙, 응급도
            모델, 병원·ETA 데이터를 결합해 병원을 추천합니다.
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

            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold">사용자 위치</p>
                  <p className="mt-1 text-xs text-slate-500">
                    입력하지 않으면 춘천시청 인근 기본 좌표로 추천합니다.
                  </p>
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
                    {groupLabel(questionResponse.symptom_group)}
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
                <h2 className="text-xl font-bold">판단 근거</h2>

                <div className="mt-4 grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl bg-slate-900 p-4 text-sm">
                    <p className="mb-2 text-slate-500">분석 방식</p>
                    <p className="font-semibold text-cyan-300">
                      {methodLabel(questionResponse.evidence.method)}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-900 p-4 text-sm">
                    <p className="mb-2 text-slate-500">학습 모델 사용</p>
                    <p className="font-semibold text-cyan-300">
                      {questionResponse.evidence.model_used ? "사용" : "미사용"}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-900 p-4 text-sm">
                    <p className="mb-2 text-slate-500">최고 유사도</p>
                    <p className="font-semibold text-cyan-300">
                      {(questionResponse.evidence.similarity_top_score * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>

                <p className="mt-4 text-sm text-slate-400">
                  {questionResponse.evidence.explanation}
                </p>
              </div>

              <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-950 p-5">
                <h2 className="text-xl font-bold">유사 실제 사례</h2>

                <div className="mt-4 space-y-3">
                  {questionResponse.similar_cases.slice(0, 3).map((item) => (
                    <div
                      key={item.case_id}
                      className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300"
                    >
                      <p className="font-medium text-slate-100">
                        {item.cleaned_text}
                      </p>

                      <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-cyan-300">
                          {item.department}
                        </span>
                        <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-cyan-300">
                          {item.suspected_disease}
                        </span>
                        <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">
                          유사도 {(item.similarity * 100).toFixed(1)}%
                        </span>
                        <span className="rounded-full bg-red-400/10 px-3 py-1 text-red-300">
                          사례 위험도 {item.severity_level} ·{" "}
                          {severityText(item.severity_level)}
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

              <div className="mb-6">
                <h2 className="text-2xl font-bold">추가 문진</h2>
                <p className="mt-2 text-sm text-slate-400">
                  증상군에 해당하는 문진 규칙 중 위험 점수가 높은 핵심 질문을
                  제시합니다.
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
                {analyzeLoading
                  ? "응급도 및 병원 분석 중..."
                  : "응급도 분석 및 병원 추천"}
              </button>

              {result && (
                <section className="mt-8 space-y-6 border-t border-slate-800 pt-8">
                  {(() => {
                    const guide = getSeverityGuide(result.severity_level);
                    const riskScore = normalizeRiskScore(result.risk_score);
                    const riskPercent = riskScore * 10;

                    return (
                      <div className={`rounded-2xl border p-5 ${guide.cardClass}`}>
                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                          <div>
                            <p className="text-sm font-semibold text-slate-300">
                              응급도 판단 결과
                            </p>

                            <div className="mt-3 flex flex-wrap items-center gap-3">
                              <span className="text-4xl" aria-hidden="true">
                                {guide.icon}
                              </span>
                              <div>
                                <p className="text-sm font-bold text-slate-300">
                                  응급도 {result.severity_level}단계 / 5단계
                                </p>
                                <h3 className="mt-1 text-4xl font-extrabold text-white">
                                  {guide.title}
                                </h3>
                              </div>
                            </div>

                            <p className="mt-4 text-lg font-bold text-white">
                              {guide.action}
                            </p>
                            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
                              {guide.description}
                            </p>
                          </div>

                          <div className="shrink-0 rounded-2xl bg-slate-950/80 p-4 text-center md:min-w-56">
                            <p className="text-xs font-semibold text-slate-400">
                              위험도 점수
                            </p>
                            <p className="mt-2 text-4xl font-extrabold text-white">
                              {riskScore}
                              <span className="text-xl text-slate-400"> / 10</span>
                            </p>
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

                        <div className="mt-5 rounded-2xl border border-slate-700/70 bg-slate-950/70 p-4">
                          <p className="font-bold text-white">응급도 단계 안내</p>
                          <p className="mt-1 text-sm text-slate-400">
                            1단계가 가장 위급하고, 5단계가 가장 낮은 응급도입니다.
                          </p>

                          <div className="mt-4 grid gap-2 text-xs md:grid-cols-5">
                            {[1, 2, 3, 4, 5].map((level) => {
                              const item = getSeverityGuide(level);
                              const active = result.severity_level === level;

                              return (
                                <div
                                  key={level}
                                  className={`rounded-xl border p-3 ${
                                    active
                                      ? "border-cyan-300 bg-cyan-400/10"
                                      : "border-slate-800 bg-slate-900/70"
                                  }`}
                                >
                                  <p className="font-bold text-white">
                                    {level}단계 · {item.title}
                                  </p>
                                  <p className="mt-1 text-slate-400">
                                    {level === 1
                                      ? "즉시 응급"
                                      : level === 2
                                        ? "빠른 진료"
                                        : level === 3
                                          ? "주의 관찰"
                                          : level === 4
                                            ? "일반 진료"
                                            : "비응급"}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                          <div className="rounded-xl bg-slate-950/70 p-3">
                            필요 자원: {result.required_resource_code}
                          </div>
                          <div className="rounded-xl bg-slate-950/70 p-3">
                            추천 진료과: {result.department}
                          </div>
                          <div className="rounded-xl bg-slate-950/70 p-3">
                            증상군: {groupLabel(result.symptom_group)}
                          </div>
                        </div>

                        <p className="mt-4 text-sm leading-6 text-slate-300">
                          {result.summary}
                        </p>
                      </div>
                    );
                  })()}

                  <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                    <h3 className="text-xl font-bold">최종 판단 근거</h3>
                    <p className="mt-3 text-sm text-slate-400">
                      {result.evidence.explanation}
                    </p>
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
                            <p>주요 진료과: {shortDepartment(hospital.department)}</p>
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
                </section>
              )}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
