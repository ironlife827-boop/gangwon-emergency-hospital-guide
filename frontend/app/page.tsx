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
  eta_source?: string;
  available_beds: number;
  recommendation_score: number;
  reason: string;
  department?: string | null;
  address?: string | null;
  phone?: string | null;
  distance_km?: number | null;
  is_emergency?: number | null;
};

type LocationSearchResult = {
  name: string;
  address: string;
  lat: number;
  lon: number;
  source: string;
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
  final_symptom_summary: string;
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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://gangwon-emergency-api.onrender.com";

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
    action: "즉시 119 신고 또는 응급실 방문이 필요합니다.",
    description: "생명에 위험할 수 있는 단계입니다. 이동 전 보호자 또는 119의 도움을 받는 것이 안전합니다.",
    cardClass: "border-red-500/70 bg-red-500/15",
    badgeClass: "bg-red-400 text-slate-950",
  },
  2: {
    icon: "⚠️",
    title: "긴급",
    action: "가능한 빨리 응급 진료를 받으세요.",
    description: "빠른 평가가 필요한 단계입니다. 증상이 악화되면 즉시 119에 연락하세요.",
    cardClass: "border-orange-400/70 bg-orange-500/15",
    badgeClass: "bg-orange-300 text-slate-950",
  },
  3: {
    icon: "🟡",
    title: "주의",
    action: "당일 또는 빠른 시간 내 진료를 권장합니다.",
    description: "현재 증상 변화에 주의가 필요합니다. 악화되면 응급실 방문을 고려하세요.",
    cardClass: "border-yellow-400/70 bg-yellow-500/15",
    badgeClass: "bg-yellow-300 text-slate-950",
  },
  4: {
    icon: "🟢",
    title: "낮음",
    action: "일반 진료 또는 외래 방문을 권장합니다.",
    description: "비교적 안정적인 단계입니다. 통증이 심해지거나 새 증상이 생기면 재평가하세요.",
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

const getSeverityGuide = (level: number) => severityGuide[level] ?? severityGuide[3];
const normalizeRiskScore = (score: number) => Math.max(0, Math.min(10, Math.round(score)));

const methodLabel = (method: string) => {
  if (method === "keyword_rule") return "고위험 키워드 안전장치";
  if (method === "trained_classifier") return "네이버 증상 데이터 기반 학습 모델";
  if (method === "trained_classifier_anchor") return "학습 모델 + 고위험 증상 보정";
  return "유사 사례 기반 추론";
};

const etaSourceLabel = (source?: string | null) => {
  if (source === "kakao_directions") return "실시간 길찾기";
  return "모델 추정";
};

export default function Home() {
  const [symptom, setSymptom] = useState("");
  const [userLat, setUserLat] = useState("");
  const [userLon, setUserLon] = useState("");
  const [locationQuery, setLocationQuery] = useState("");
  const [locationResults, setLocationResults] = useState<LocationSearchResult[]>([]);
  const [questionResponse, setQuestionResponse] = useState<QuestionResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<TriageResult | null>(null);

  const [questionLoading, setQuestionLoading] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationSearchLoading, setLocationSearchLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const numericLat = userLat.trim() ? Number(userLat) : null;
  const numericLon = userLon.trim() ? Number(userLon) : null;

  const resetConsultation = () => {
    setQuestionResponse(null);
    setAnswers({});
    setResult(null);
    setErrorMessage("");
  };

  const startNewConsultation = () => {
    setSymptom("");
    setQuestionResponse(null);
    setAnswers({});
    setResult(null);
    setLocationQuery("");
    setLocationResults([]);
    setErrorMessage("");
  };

  const handleSearchLocation = async () => {
    const query = locationQuery.trim();
    if (query.length < 2) {
      setErrorMessage("주소나 장소명을 두 글자 이상 입력해 주세요.");
      return;
    }

    setLocationSearchLoading(true);
    setErrorMessage("");
    setLocationResults([]);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/location/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail ?? "위치 검색에 실패했습니다.");
      }

      const data = await response.json();
      setLocationResults(data.results ?? []);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "위치 검색 결과를 불러오지 못했습니다. 더 구체적인 주소나 장소명을 입력해 주세요."
      );
    } finally {
      setLocationSearchLoading(false);
    }
  };

  const handleSelectLocation = (item: LocationSearchResult) => {
    setUserLat(item.lat.toFixed(6));
    setUserLon(item.lon.toFixed(6));
    setLocationQuery(item.name || item.address);
    setLocationResults([]);
    resetConsultation();
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
      <section className="mx-auto max-w-5xl px-5 py-8 md:px-6 md:py-10">
        <header className="mb-8 text-center">
          <p className="mb-3 text-sm font-semibold text-cyan-400">
            Gangwon Emergency Hospital Guide
          </p>

          <h1 className="text-3xl font-bold leading-tight md:text-5xl">
            강원도 맞춤형 응급 및
            <br />
            상시 병원 안내 시스템
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-sm leading-6 text-slate-300 md:text-base">
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
              placeholder="예: 갑자기 왼팔에 힘이 안 들어가고 말이 어눌해요."
            />

            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold">사용자 위치</p>
                  <p className="mt-1 text-xs text-slate-500">
                    위치를 입력하면 가까운 병원을 우선 추천합니다.
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

              <div className="mb-3 flex flex-col gap-2 md:flex-row">
                <input
                  value={locationQuery}
                  onChange={(event) => setLocationQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      handleSearchLocation();
                    }
                  }}
                  className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                  placeholder="주소나 장소명 검색 예: 강원대학교병원, 춘천시청"
                />

                <button
                  type="button"
                  onClick={handleSearchLocation}
                  disabled={locationSearchLoading}
                  className="rounded-xl border border-slate-600 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300 disabled:cursor-not-allowed disabled:text-slate-500"
                >
                  {locationSearchLoading ? "검색 중..." : "지도 검색"}
                </button>
              </div>

              {locationResults.length > 0 && (
                <div className="mb-3 space-y-2">
                  {locationResults.map((item) => (
                    <button
                      key={`${item.lat}-${item.lon}-${item.name}`}
                      type="button"
                      onClick={() => handleSelectLocation(item)}
                      className="w-full rounded-xl border border-slate-800 bg-slate-900 px-4 py-3 text-left transition hover:border-cyan-400"
                    >
                      <span className="block text-sm font-semibold text-white">{item.name}</span>
                      <span className="mt-1 block text-xs text-slate-400">{item.address}</span>
                    </button>
                  ))}
                </div>
              )}

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

          {questionResponse && (
            <div className="border-t border-slate-800 pt-7">
              {!result && (
                <>
                  <div className="mb-5 rounded-2xl border border-cyan-400/30 bg-cyan-400/10 p-4">
                    <p className="text-sm font-semibold text-cyan-300">추가 확인이 필요합니다</p>
                    <p className="mt-1 text-sm text-slate-300">
                      입력한 증상에서 부족한 정보만 확인합니다. 답변 후 최종 응급도와 병원을 안내합니다.
                    </p>
                  </div>

                  <div className="space-y-4">
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
                    className="mt-6 w-full rounded-2xl bg-white px-6 py-4 font-bold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                  >
                    {analyzeLoading ? "응급도 및 병원 분석 중..." : "최종 결과 보기"}
                  </button>
                </>
              )}

              {result && (
                <section className="space-y-5">
                  {(() => {
                    const guide = getSeverityGuide(result.severity_level);
                    const riskScore = normalizeRiskScore(result.risk_score);
                    const riskPercent = riskScore * 10;
                    const topHospital = result.hospitals[0];
                    const otherHospitals = result.hospitals.slice(1);

                    return (
                      <>
                        <div className={`rounded-3xl border p-5 md:p-6 ${guide.cardClass}`}>
                          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                            <div>
                              <p className="text-sm font-semibold text-slate-300">최종 응급도</p>
                              <div className="mt-3 flex items-center gap-3">
                                <span className="text-5xl" aria-hidden="true">{guide.icon}</span>
                                <div>
                                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${guide.badgeClass}`}>
                                    {result.severity_level}단계 / 5단계
                                  </span>
                                  <h2 className="mt-2 text-4xl font-extrabold text-white">{guide.title}</h2>
                                </div>
                              </div>
                              <p className="mt-4 text-xl font-bold text-white">{guide.action}</p>
                              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">{guide.description}</p>
                            </div>

                            <div className="rounded-2xl bg-slate-950/80 p-4 md:min-w-60">
                              <div className="flex items-end justify-between gap-4">
                                <p className="text-sm font-semibold text-slate-400">위험도</p>
                                <p className="text-3xl font-extrabold text-white">
                                  {riskScore}<span className="text-lg text-slate-400"> / 10</span>
                                </p>
                              </div>
                              <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-800">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-yellow-300 to-red-500"
                                  style={{ width: `${riskPercent}%` }}
                                />
                              </div>
                              <p className="mt-2 text-xs text-slate-500">10점에 가까울수록 위험도가 높습니다.</p>
                            </div>
                          </div>
                        </div>

                        <div className="grid gap-4 md:grid-cols-3">
                          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                            <p className="text-xs text-slate-500">의심 질환</p>
                            <p className="mt-2 text-xl font-bold text-cyan-300">{result.suspected_disease}</p>
                          </div>
                          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                            <p className="text-xs text-slate-500">추천 진료과</p>
                            <p className="mt-2 text-xl font-bold text-cyan-300">{result.department}</p>
                          </div>
                          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                            <p className="text-xs text-slate-500">증상군</p>
                            <p className="mt-2 text-xl font-bold text-cyan-300">{groupLabel(result.symptom_group)}</p>
                          </div>
                        </div>

                        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                          <p className="text-xs text-slate-500">판단 요약</p>
                          <p className="mt-2 text-sm leading-6 text-slate-300">{result.summary}</p>
                        </div>

                        {topHospital && (
                          <div className="rounded-3xl border border-cyan-400/40 bg-cyan-400/10 p-5 md:p-6">
                            <p className="text-sm font-semibold text-cyan-300">가장 먼저 확인할 병원</p>
                            <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                              <div>
                                <h3 className="text-2xl font-extrabold text-white">{topHospital.hospital_name}</h3>
                                <p className="mt-2 text-sm text-slate-300">{topHospital.reason}</p>
                                {topHospital.address && (
                                  <p className="mt-3 text-sm text-slate-400">{topHospital.address}</p>
                                )}
                                {topHospital.phone && (
                                  <p className="mt-1 text-sm text-slate-400">전화: {topHospital.phone}</p>
                                )}
                              </div>
                              <div className="grid min-w-48 grid-cols-2 gap-2 text-sm md:text-right">
                                <div className="rounded-xl bg-slate-950/70 p-3">
                                  <p className="text-xs text-slate-500">예상 이동</p>
                                  <p className="mt-1 font-bold text-white">{topHospital.eta_min}분</p>
                                  <p className="mt-1 text-[11px] text-slate-500">
                                    {etaSourceLabel(topHospital.eta_source)}
                                  </p>
                                </div>
                                <div className="rounded-xl bg-slate-950/70 p-3">
                                  <p className="text-xs text-slate-500">거리</p>
                                  <p className="mt-1 font-bold text-white">{topHospital.distance_km}km</p>
                                </div>
                                <div className="col-span-2 rounded-xl bg-slate-950/70 p-3">
                                  <p className="text-xs text-slate-500">응급 병상</p>
                                  <p className="mt-1 font-bold text-white">{topHospital.available_beds}개</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {otherHospitals.length > 0 && (
                          <details className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                            <summary className="cursor-pointer text-lg font-bold text-white">
                              다른 추천 병원 보기
                            </summary>
                            <div className="mt-4 grid gap-3 md:grid-cols-2">
                              {otherHospitals.map((hospital) => (
                                <article
                                  key={`${hospital.rank}-${hospital.hospital_name}`}
                                  className="rounded-2xl border border-slate-800 bg-slate-900 p-4"
                                >
                                  <p className="text-sm font-semibold text-cyan-300">추천 {hospital.rank}순위</p>
                                  <h4 className="mt-1 text-lg font-bold">{hospital.hospital_name}</h4>
                                  <div className="mt-3 space-y-1 text-sm text-slate-300">
                                    <p>주요 진료과: {shortDepartment(hospital.department)}</p>
                                    <p>
                                      예상 이동시간: {hospital.eta_min}분 · {etaSourceLabel(hospital.eta_source)}
                                    </p>
                                    <p>거리: {hospital.distance_km}km</p>
                                    <p>응급 병상: {hospital.available_beds}개</p>
                                  </div>
                                  {hospital.address && (
                                    <p className="mt-3 text-xs text-slate-500">{hospital.address}</p>
                                  )}
                                </article>
                              ))}
                            </div>
                          </details>
                        )}

                        <details className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                          <summary className="cursor-pointer text-lg font-bold text-white">
                            분석 근거와 실제 유사 사례 보기
                          </summary>

                          <div className="mt-4 rounded-2xl bg-slate-900 p-4 text-sm text-slate-300">
                            <p className="font-semibold text-white">판단 방식</p>
                            <p className="mt-2">{methodLabel(result.evidence.method)}</p>
                            <p className="mt-2 text-slate-400">{result.evidence.explanation}</p>
                          </div>

                          <div className="mt-4 rounded-2xl bg-slate-900 p-4 text-sm text-slate-300">
                            <p className="font-semibold text-white">최종 분석 문장</p>
                            <p className="mt-2 leading-6 text-slate-400">{result.final_symptom_summary}</p>
                          </div>

                          <div className="mt-4 space-y-3">
                            {result.similar_cases.slice(0, 3).map((item) => (
                              <div
                                key={item.case_id}
                                className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300"
                              >
                                <p className="font-medium text-slate-100">{item.cleaned_text}</p>

                                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                                  <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-cyan-300">
                                    {item.suspected_disease === result.suspected_disease
                                      ? "동일 질환 사례"
                                      : `${groupLabel(item.symptom_group)} 관련 사례`}
                                  </span>
                                  <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">
                                    {item.department}
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
                        </details>

                        <button
                          type="button"
                          onClick={startNewConsultation}
                          className="w-full rounded-2xl border border-slate-700 px-6 py-4 font-bold text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300"
                        >
                          새 증상 입력하기
                        </button>
                      </>
                    );
                  })()}
                </section>
              )}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
