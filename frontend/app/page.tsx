export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto max-w-7xl px-6 py-10">
        <header className="mb-10">
          <p className="mb-3 text-sm font-semibold text-cyan-400">
            Gangwon Emergency Hospital Guide
          </p>

          <h1 className="text-4xl font-bold leading-tight md:text-6xl">
            강원도 맞춤형 응급 및<br />
            상시 병원 안내 시스템
          </h1>

          <p className="mt-5 max-w-3xl text-slate-300 md:text-lg">
            생성형 AI는 사용자의 증상을 문진 질문과 구조화된 피처로 변환하고,
            최종 응급도 판단과 병원 추천은 자체 데이터셋과 모델 기반으로 수행합니다.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1fr_420px]">
          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-4 text-2xl font-bold">1. 증상 입력</h2>

              <textarea
                className="min-h-32 w-full rounded-2xl border border-slate-700 bg-slate-950 p-4 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                placeholder="예: 갑자기 가슴이 답답하고 숨쉬기가 어려워요."
              />

              <button className="mt-4 rounded-2xl bg-cyan-400 px-6 py-3 font-bold text-slate-950 hover:bg-cyan-300">
                AI 문진 시작
              </button>
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-4 text-2xl font-bold">2. AI 문진 질문</h2>

              <div className="space-y-4">
                {[
                  "증상이 언제부터 시작되었나요?",
                  "호흡곤란, 식은땀, 어지러움이 동반되나요?",
                  "통증의 강도를 1~10점으로 표현하면 몇 점인가요?",
                  "기저질환이나 복용 중인 약이 있나요?",
                ].map((question, index) => (
                  <div
                    key={question}
                    className="rounded-2xl border border-slate-800 bg-slate-950 p-4"
                  >
                    <p className="mb-3 text-sm font-semibold text-cyan-300">
                      Q{index + 1}. {question}
                    </p>
                    <input
                      className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-cyan-400"
                      placeholder="답변을 입력하세요."
                    />
                  </div>
                ))}
              </div>

              <button className="mt-5 w-full rounded-2xl bg-white px-6 py-4 font-bold text-slate-950 hover:bg-slate-200">
                응급도 분석 및 병원 추천
              </button>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-4 text-xl font-bold">처리 흐름</h2>

              <ol className="space-y-3 text-sm text-slate-300">
                <li>1. 사용자 자유 증상 입력</li>
                <li>2. OpenAI API 기반 문진 질문 생성</li>
                <li>3. 답변을 구조화된 피처로 변환</li>
                <li>4. severity_model.pkl로 응급도 판단</li>
                <li>5. 필요 의료자원 코드 추론</li>
                <li>6. 실시간 병상 API 확인</li>
                <li>7. eta_model.pkl로 예상 이동시간 계산</li>
                <li>8. 병원 랭킹 및 지도 시각화</li>
              </ol>
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-4 text-xl font-bold">AI 역할 제한</h2>

              <div className="space-y-3 text-sm text-slate-300">
                <p>
                  AI는 의료 판단을 직접 수행하지 않고, 사용자의 자연어 증상을
                  문진 질문과 모델 입력 피처로 변환합니다.
                </p>
                <p>
                  최종 응급도와 병원 추천은 팀 데이터셋, 모델, 추천 알고리즘을
                  기반으로 산출합니다.
                </p>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-4 text-xl font-bold">예상 피처</h2>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-slate-950 p-3">symptom_group</div>
                <div className="rounded-xl bg-slate-950 p-3">risk_score</div>
                <div className="rounded-xl bg-slate-950 p-3">duration_min</div>
                <div className="rounded-xl bg-slate-950 p-3">pain_level</div>
                <div className="rounded-xl bg-slate-950 p-3">resource_code</div>
                <div className="rounded-xl bg-slate-950 p-3">severity</div>
              </div>
            </div>
          </aside>
        </section>
      </section>
    </main>
  );
}
