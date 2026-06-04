"use client";

import { useState } from "react";

const questions = [
  {
    question: "증상이 언제부터 시작되었나요?",
    options: ["방금 전", "1시간 이내", "오늘 중", "며칠 전부터"],
  },
  {
    question: "현재 증상의 정도는 어떤가요?",
    options: ["가벼움", "참을 수 있음", "심함", "매우 심함"],
  },
  {
    question: "동반 증상이 있나요?",
    options: ["없음", "어지러움", "호흡곤란", "의식 저하"],
  },
  {
    question: "현재 혼자 이동할 수 있나요?",
    options: ["가능함", "조금 어려움", "거의 불가능", "도움이 필요함"],
  },
];

export default function Home() {
  const [symptom, setSymptom] = useState("");
  const [started, setStarted] = useState(false);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [customAnswers, setCustomAnswers] = useState<Record<number, string>>({});

  const handleSelect = (questionIndex: number, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionIndex]: value,
    }));
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
              onChange={(e) => setSymptom(e.target.value)}
              className="min-h-32 w-full rounded-2xl border border-slate-700 bg-slate-950 p-4 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
              placeholder="예: 갑자기 가슴이 답답하고 숨쉬기가 어려워요."
            />

            <button
              onClick={() => setStarted(true)}
              disabled={!symptom.trim()}
              className="mt-4 rounded-2xl bg-cyan-400 px-6 py-3 font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              AI 문진 시작
            </button>
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
                    key={item.question}
                    className="rounded-2xl border border-slate-800 bg-slate-950 p-5"
                  >
                    <p className="mb-4 font-semibold">
                      Q{index + 1}. {item.question}
                    </p>

                    <div className="grid gap-3 md:grid-cols-2">
                      {item.options.map((option) => (
                        <button
                          key={option}
                          onClick={() => handleSelect(index, option)}
                          className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
                            answers[index] === option
                              ? "border-cyan-400 bg-cyan-400 text-slate-950"
                              : "border-slate-700 bg-slate-900 text-slate-300 hover:border-cyan-400"
                          }`}
                        >
                          {option}
                        </button>
                      ))}

                      <button
                        onClick={() => handleSelect(index, "기타")}
                        className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
                          answers[index] === "기타"
                            ? "border-cyan-400 bg-cyan-400 text-slate-950"
                            : "border-slate-700 bg-slate-900 text-slate-300 hover:border-cyan-400"
                        }`}
                      >
                        기타 직접 입력
                      </button>
                    </div>

                    {answers[index] === "기타" && (
                      <input
                        value={customAnswers[index] ?? ""}
                        onChange={(e) =>
                          setCustomAnswers((prev) => ({
                            ...prev,
                            [index]: e.target.value,
                          }))
                        }
                        className="mt-4 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                        placeholder="직접 답변을 입력하세요."
                      />
                    )}
                  </div>
                ))}
              </div>

              <button className="mt-8 w-full rounded-2xl bg-white px-6 py-4 font-bold text-slate-950 transition hover:bg-slate-200">
                응급도 분석 및 병원 추천
              </button>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
