export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-10">
        <header className="mb-10">
          <p className="mb-3 text-sm font-semibold text-cyan-400">
            Gangwon Emergency Hospital Guide
          </p>

          <h1 className="text-4xl font-bold leading-tight md:text-6xl">
            강원도 맞춤형 응급 및<br />
            상시 병원 안내 시스템
          </h1>

          <p className="mt-5 max-w-2xl text-base text-slate-300 md:text-lg">
            증상 문진, 응급도 판단, 실시간 병상 정보, 예상 이동시간을
            통합하여 현재 상황에 적합한 병원을 추천합니다.
          </p>
        </header>

        <section className="grid flex-1 gap-6 md:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl">
            <h2 className="mb-4 text-2xl font-bold">증상 입력</h2>

            <textarea
              className="min-h-40 w-full rounded-2xl border border-slate-700 bg-slate-950 p-4 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-400"
              placeholder="예: 갑자기 가슴이 답답하고 숨쉬기가 어려워요."
            />

            <button className="mt-4 w-full rounded-2xl bg-cyan-400 px-5 py-4 font-bold text-slate-950 transition hover:bg-cyan-300">
              문진 시작하기
            </button>
          </div>

          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-3 text-xl font-bold">시스템 흐름</h2>

              <ol className="space-y-3 text-sm text-slate-300">
                <li>1. 사용자 증상 입력</li>
                <li>2. 챗봇 문진</li>
                <li>3. 응급도 판단</li>
                <li>4. 필요 의료자원 추론</li>
                <li>5. 실시간 병상 확인</li>
                <li>6. ETA 계산</li>
                <li>7. 병원 랭킹 및 지도 시각화</li>
              </ol>
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
              <h2 className="mb-3 text-xl font-bold">평가 포인트</h2>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-2xl bg-slate-950 p-4">데이터 통합</div>
                <div className="rounded-2xl bg-slate-950 p-4">피처 엔지니어링</div>
                <div className="rounded-2xl bg-slate-950 p-4">모델링</div>
                <div className="rounded-2xl bg-slate-950 p-4">추천 알고리즘</div>
              </div>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}