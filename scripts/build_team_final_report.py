from __future__ import annotations

import html
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ASSETS = REPORTS / "team_report_assets"
HTML_PATH = REPORTS / "team_final_report.html"
PDF_PATH = REPORTS / "team_final_report.pdf"

FONT_PATH = Path("C:/Windows/Fonts/malgun.ttf")
BOLD_FONT_PATH = Path("C:/Windows/Fonts/malgunbd.ttf")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_FONT_PATH if bold else FONT_PATH), size)


def save_chart_data_summary() -> None:
    df = pd.read_csv(ROOT / "data/processed/naver_kin_symptom_cases_mapped.csv")
    counts = df["symptom_group"].value_counts().head(10).sort_values()
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
    colors = ["#12c6dc" if i >= len(counts) - 3 else "#d5e2ef" for i in range(len(counts))]
    ax.barh(counts.index, counts.values, color=colors)
    ax.set_title("증상군별 데이터 분포 TOP10", fontsize=16, weight="bold", pad=14)
    ax.set_xlabel("사례 수")
    ax.grid(axis="x", alpha=0.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    for y, v in enumerate(counts.values):
        ax.text(v + 8, y, f"{v:,}", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(ASSETS / "symptom_group_distribution.png", transparent=False, facecolor="white")
    plt.close(fig)


def save_model_comparison_chart() -> None:
    df = pd.read_csv(ROOT / "data/processed/model_evaluation/model_comparison_summary.csv")
    pivot = df.pivot(index="model", columns="target", values="accuracy").loc[
        [
            "baseline_most_frequent",
            "word_tfidf_logreg",
            "char_tfidf_logreg",
            "char_tfidf_linear_svc",
        ]
    ]
    labels = ["Baseline", "Word TF-IDF", "Char TF-IDF", "Char TF-IDF+SVC"]
    targets = ["symptom_group", "department", "suspected_disease"]
    x = range(len(labels))
    plt.rcParams["font.family"] = "Malgun Gothic"
    fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
    width = 0.23
    colors = ["#12c6dc", "#25d0a0", "#ff4d5d"]
    for i, target in enumerate(targets):
        ax.bar([n + (i - 1) * width for n in x], pivot[target], width, label=target, color=colors[i])
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylim(0, 1.08)
    ax.set_title("모델별 정확도 비교", fontsize=16, weight="bold", pad=14)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    for i, target in enumerate(targets):
        for n, v in enumerate(pivot[target]):
            ax.text(n + (i - 1) * width, v + 0.015, f"{v:.2f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(ASSETS / "model_comparison_accuracy.png", transparent=False, facecolor="white")
    plt.close(fig)


def save_data_role_diagram() -> None:
    img = Image.new("RGB", (1600, 900), "#f3f7fb")
    d = ImageDraw.Draw(img)
    title_font = font(54, True)
    head_font = font(25, True)
    body_font = font(24)
    d.text((80, 70), "데이터별 역할 분리", fill="#10213b", font=title_font)
    d.text((82, 140), "질환 판단 데이터와 응급도 보조 데이터를 분리하여 모델 흔들림을 줄임", fill="#61728a", font=font(26))
    cards = [
        ("네이버 지식인", "자연어 증상 표현\n모델 학습 중심", "#12c6dc"),
        ("질환 마스터", "disease_id 기준\n라벨 통합", "#25d0a0"),
        ("질환백과 지식", "질환명·증상·진료과\n체계 보강", "#8e6cff"),
        ("문진/응급 룰", "risk_score 기반\n위험도 보조", "#ffc247"),
        ("병원/병상 데이터", "진료과·거리·ETA·병상\n추천 점수 계산", "#2b6eff"),
    ]
    for i, (h, b, c) in enumerate(cards):
        x = 90 + i * 300
        y = 300 if i % 2 == 0 else 390
        d.rounded_rectangle((x, y, x + 250, y + 230), radius=34, fill="white", outline="#cfe0ee", width=3)
        d.rounded_rectangle((x + 18, y + 32, x + 232, y + 86), radius=26, fill=c)
        d.text((x + 125, y + 58), h, fill="white" if c in ["#8e6cff", "#2b6eff"] else "#10213b", font=head_font, anchor="mm")
        d.multiline_text((x + 125, y + 150), b, fill="#10213b", font=body_font, anchor="mm", align="center", spacing=8)
    d.rounded_rectangle((310, 730, 1290, 810), radius=30, fill="#07162d")
    d.text((800, 770), "최종 출력: 의심 질환 · 응급도 · 추천 진료과 · 병원 추천", fill="white", font=font(32, True), anchor="mm")
    img.save(ASSETS / "data_role_diagram.png")


def save_system_pipeline_diagram() -> None:
    img = Image.new("RGB", (1600, 760), "#f3f7fb")
    d = ImageDraw.Draw(img)
    d.text((80, 62), "전체 시스템 파이프라인", fill="#10213b", font=font(52, True))
    d.text((82, 130), "사용자 증상 입력부터 최종 병원 추천까지 하나의 흐름으로 연결", fill="#61728a", font=font(25))

    steps = [
        ("증상 입력", "자연어 문장\n위치 설정", "#12c6dc"),
        ("모델 예측", "증상군·진료과\n질환 TOP3", "#25d0a0"),
        ("추가 문진", "질환별 질문\nTop 1~4", "#ffc247"),
        ("응급도 계산", "red flag\nrisk_score", "#ff4d5d"),
        ("병원 추천", "진료과·병상\n거리·ETA", "#2b6eff"),
    ]
    y = 330
    for i, (head, body, color) in enumerate(steps):
        x = 85 + i * 300
        d.rounded_rectangle((x, y, x + 230, y + 190), radius=28, fill="white", outline="#cfe0ee", width=3)
        d.rounded_rectangle((x + 30, y + 30, x + 200, y + 82), radius=24, fill=color)
        d.text((x + 115, y + 56), head, fill="white" if color in ["#ff4d5d", "#2b6eff"] else "#10213b", font=font(25, True), anchor="mm")
        d.multiline_text((x + 115, y + 130), body, fill="#10213b", font=font(24, True), anchor="mm", align="center", spacing=7)
        if i < len(steps) - 1:
            x1 = x + 242
            x2 = x + 288
            d.line((x1, y + 95, x2, y + 95), fill="#12c6dc", width=8)
            d.polygon([(x2, y + 95), (x2 - 20, y + 82), (x2 - 20, y + 108)], fill="#12c6dc")

    d.rounded_rectangle((235, 610, 1365, 690), radius=30, fill="#07162d")
    d.text((800, 650), "질환 예측은 모델 중심 · 응급도 데이터는 위험도 계산 보조", fill="white", font=font(31, True), anchor="mm")
    img.save(ASSETS / "system_pipeline_diagram.png")


def save_cover_icon() -> None:
    src = ROOT / "frontend/public/app-icon.png"
    if src.exists():
        icon = Image.open(src).convert("RGBA")
        icon.thumbnail((360, 360))
        canvas = Image.new("RGBA", (420, 420), (255, 255, 255, 0))
        canvas.alpha_composite(icon, ((420 - icon.width) // 2, (420 - icon.height) // 2))
        canvas.save(ASSETS / "app_icon.png")


def save_service_input_mock() -> None:
    img = Image.new("RGB", (1500, 820), "#07162d")
    d = ImageDraw.Draw(img)
    d.text((80, 70), "증상 입력 화면", fill="white", font=font(48, True))
    d.text((82, 130), "사용자는 자연어 증상과 위치만 입력하면 문진을 시작할 수 있음", fill="#9fc8d4", font=font(25))
    d.rounded_rectangle((95, 210, 1405, 710), radius=34, fill="#111d34", outline="#2a4263", width=3)
    d.text((145, 265), "증상 입력", fill="white", font=font(31, True))
    d.rounded_rectangle((145, 320, 1355, 455), radius=18, fill="#071126", outline="#395171", width=2)
    d.multiline_text(
        (180, 350),
        "갑자기 한쪽 팔에 힘이 빠지고 말이 어눌해졌습니다.",
        fill="white",
        font=font(28, True),
        spacing=6,
    )
    d.text((145, 510), "사용자 위치", fill="white", font=font(27, True))
    d.rounded_rectangle((145, 555, 980, 615), radius=15, fill="#16243b", outline="#3e5878", width=2)
    d.text((170, 585), "주소나 장소명 검색 예: 강원대학교병원, 춘천시청", fill="#9fb0c7", font=font(22), anchor="lm")
    d.rounded_rectangle((1010, 555, 1230, 615), radius=15, fill="#071126", outline="#12c6dc", width=2)
    d.text((1120, 585), "지도 검색", fill="white", font=font(23, True), anchor="mm")
    d.rounded_rectangle((145, 645, 335, 700), radius=22, fill="#12c6dc")
    d.text((240, 672), "문진 시작", fill="#07162d", font=font(24, True), anchor="mm")
    img.save(ASSETS / "service_input_mock.png")


def save_service_result_mock() -> None:
    img = Image.new("RGB", (1500, 900), "#07162d")
    d = ImageDraw.Draw(img)
    d.text((80, 60), "분석 결과 화면", fill="white", font=font(48, True))
    d.text((82, 120), "응급도, 의심 질환, 추천 진료과, 병원 추천을 한 화면에서 제공", fill="#9fc8d4", font=font(25))
    d.rounded_rectangle((95, 190, 1405, 395), radius=32, fill="#341525", outline="#ff4d5d", width=3)
    d.text((145, 240), "최종 응급도", fill="white", font=font(24, True))
    d.text((145, 305), "매우 긴급", fill="white", font=font(50, True))
    d.rounded_rectangle((1130, 240, 1325, 345), radius=20, fill="#071126")
    d.text((1228, 285), "위험도", fill="#9fc8d4", font=font(20, True), anchor="mm")
    d.text((1228, 323), "9 / 10", fill="white", font=font(31, True), anchor="mm")
    cards = [
        ("의심 질환", "뇌졸중", "#12c6dc"),
        ("추천 진료과", "신경과 / 응급의학과", "#25d0a0"),
        ("증상군", "신경계", "#ffc247"),
    ]
    for i, (h, b, c) in enumerate(cards):
        x = 95 + i * 435
        d.rounded_rectangle((x, 430, x + 390, 560), radius=24, fill="#0b1429", outline="#253a58", width=2)
        d.text((x + 35, 470), h, fill="#9fb0c7", font=font(19, True))
        d.text((x + 35, 520), b, fill=c, font=font(28, True))
    d.rounded_rectangle((95, 600, 1405, 820), radius=30, fill="#073044", outline="#12c6dc", width=3)
    d.text((145, 655), "가장 먼저 확인할 병원", fill="#7bf2ff", font=font(24, True))
    d.text((145, 720), "한림대학교춘천성심병원", fill="white", font=font(38, True))
    d.text((145, 770), "응급실 보유 · 신경계 진료과 매칭 · 예상 이동시간 8분", fill="#c5e5ee", font=font(24))
    d.rounded_rectangle((1080, 695, 1300, 765), radius=18, fill="#071126", outline="#2b6eff", width=2)
    d.text((1190, 730), "카카오맵 경로 보기", fill="white", font=font(22, True), anchor="mm")
    img.save(ASSETS / "service_result_mock.png")


def save_code_snippet_image(filename: str, title: str, code: str) -> None:
    lines = code.strip("\n").splitlines()
    line_h = 34
    w = 1500
    h = 130 + line_h * len(lines)
    img = Image.new("RGB", (w, h), "#07162d")
    d = ImageDraw.Draw(img)
    d.text((48, 34), title, fill="#8cecff", font=font(30, True))
    code_font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 24)
    y = 92
    for i, line in enumerate(lines, start=1):
        d.text((45, y), f"{i:02d}", fill="#7890aa", font=code_font)
        d.text((105, y), line.replace("\t", "    "), fill="#f5f7ff", font=code_font)
        y += line_h
    img.save(ASSETS / filename)


def generate_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    save_cover_icon()
    save_chart_data_summary()
    save_model_comparison_chart()
    save_data_role_diagram()
    save_system_pipeline_diagram()
    save_service_input_mock()
    save_service_result_mock()
    save_code_snippet_image(
        "code_model_training.png",
        "모델 학습 코드 핵심",
        """
model = Pipeline([
    ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 5))),
    ("clf", LinearSVC(class_weight="balanced", random_state=42)),
])

model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred, zero_division=0))
""",
    )
    save_code_snippet_image(
        "code_question_ranking.png",
        "문진 질문 랭킹 코드 핵심",
        """
score = (
    disease_id_match * 45
    + disease_match * 40
    + group_match * 5
    + risk_score * 2.5
    + importance * 2
    - already_mentioned_penalty
)
""",
    )
    save_code_snippet_image(
        "code_hospital_ranking.png",
        "병원 추천 코드 핵심",
        """
hospitals["recommendation_score"] = (
    hospitals["department_score"] * 35
    + hospitals["bed_score"] * 25
    + hospitals["emergency_score"] * 20
    - hospitals["eta_min"] * 1.2
)
""",
    )


def img_tag(path: str, caption: str) -> str:
    return f"""
    <figure>
      <img src="{html.escape(path)}" alt="{html.escape(caption)}">
      <figcaption>{html.escape(caption)}</figcaption>
    </figure>
    """


def table_html(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def build_html() -> str:
    eval_df = pd.read_csv(ROOT / "data/processed/model_evaluation/model_comparison_summary.csv")
    best_rows = []
    for target in ["symptom_group", "department", "suspected_disease"]:
        row = eval_df[eval_df["target"] == target].sort_values(["accuracy", "macro_f1"], ascending=False).iloc[0]
        best_rows.append([target, row["model"], f"{row['accuracy']:.4f}", f"{row['macro_f1']:.4f}", int(row["classes"])])

    data_rows = [
        ["네이버 지식인 증상 사례", "3,499건", "자연어 증상 표현 학습"],
        ["disease_master", "149개 질환", "질환명·별칭·진료과 통합"],
        ["disease_question_map", "532문항", "질환별 추가 문진 후보"],
        ["triage_rule_dataset", "113개 룰", "응급도 risk_score 보조"],
        ["hospital_master", "1,994개 병원", "상시/응급 병원 추천"],
        ["gangwon_hospital_with_beds", "24개 응급기관", "응급 병상 fallback"],
    ]
    file_rows = [
        ["backend/", "FastAPI 라우터, 분석/문진/추천 서비스"],
        ["frontend/", "사용자 입력, 문진, 결과 UI"],
        ["data_pipeline/", "수집·정제·라벨 매핑·학습 코드"],
        ["data/processed/", "실제 서비스와 학습에 쓰는 CSV"],
        ["models/", "symptom_classifier.pkl, eta_model.pkl"],
        ["archive/", "과거 실험/레거시 자료 보관"],
    ]

    css = """
    @page { size: A4; margin: 13mm 13mm 14mm 13mm; }
    * { box-sizing: border-box; }
    body { margin: 0; color: #101d33; font-family: "Malgun Gothic", "맑은 고딕", sans-serif; font-size: 11pt; line-height: 1.55; background: #e9eef5; }
    .page { width: 210mm; min-height: 297mm; margin: 0 auto 10px auto; padding: 15mm 15mm 15mm 15mm; background: white; page-break-after: always; position: relative; overflow: visible; }
    .cover { background: white; color: #101d33; border-top: 10px solid #12c6dc; }
    h1 { font-size: 25pt; margin: 0 0 7mm 0; letter-spacing: 0; }
    h2 { font-size: 18pt; margin: 0 0 5mm 0; color: #07162d; }
    h3 { font-size: 13pt; margin: 5mm 0 2mm 0; color: #17385e; }
    p { margin: 0 0 3.2mm 0; }
    .lead { font-size: 13pt; color: #5a6a80; }
    .cover .lead { color: #61728a; }
    .toc-line { display: flex; justify-content: space-between; border-bottom: 1px dotted #aab8ca; padding: 2.4mm 0; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; align-items: start; }
    .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; }
    .card { border: 1px solid #d7e2ef; border-radius: 8px; padding: 4mm; background: #f8fbff; }
    .metric { font-size: 20pt; font-weight: 700; color: #05bcd6; }
    figure { margin: 4mm 0; }
    img { width: 100%; max-height: 86mm; object-fit: contain; border-radius: 6px; border: 1px solid #d6e1ef; display: block; }
    figcaption { font-size: 9.5pt; color: #607089; margin-top: 1.5mm; text-align: center; }
    table { width: 100%; border-collapse: collapse; margin: 3mm 0 5mm 0; font-size: 9.6pt; }
    th { background: #07162d; color: white; padding: 2.2mm; text-align: left; }
    td { border: 1px solid #dbe4ef; padding: 2mm; vertical-align: top; }
    ul { margin: 1mm 0 3mm 5mm; padding-left: 4mm; }
    li { margin-bottom: 1.5mm; }
    .tag { display: inline-block; border-radius: 999px; background: #eafcff; color: #08788d; font-weight: 700; padding: 1.2mm 3mm; margin: 0 1mm 1.5mm 0; }
    .note { background: #fff8df; border-left: 4px solid #ffc247; padding: 3mm; border-radius: 5px; }
    .analysis-box { background: #f4f8fc; border: 1px solid #d9e5f1; border-radius: 8px; padding: 3.2mm; margin: 3mm 0; }
    .analysis-box b { color: #07162d; }
    .footer { position: absolute; bottom: 7mm; left: 15mm; right: 15mm; color: #93a2b5; font-size: 9pt; display: flex; justify-content: space-between; }
    .cover-title { margin-top: 28mm; font-size: 30pt; line-height: 1.25; }
    .cover-box { margin-top: 18mm; border: 1px solid #d7e2ef; border-radius: 10px; padding: 8mm; background: #f8fbff; }
    .cover-icon { width: 42mm; height: 42mm; object-fit: contain; border: 0; border-radius: 14mm; margin: 0 0 14mm auto; display: block; }
    .small { font-size: 9.5pt; color: #61728a; }
    .report-shots { gap: 3mm; }
    .report-shots figure { margin: 3mm 0; }
    .report-shots img { max-height: 58mm; }
    """

    pages: list[str] = []

    def page(title: str, body: str, num: str = "") -> None:
        pages.append(f'<section class="page"><h2>{title}</h2>{body}<div class="footer"><span>강원도 맞춤형 응급 및 상시 병원 안내 시스템</span><span>{num}</span></div></section>')

    pages.append(
        """
        <section class="page cover">
          <img class="cover-icon" src="team_report_assets/app_icon.png" alt="앱 아이콘">
          <div class="cover-title">강원도 맞춤형<br>응급 및 상시 병원 안내 시스템</div>
          <p class="lead">자연어 증상 분류 모델과 실시간 병원 추천 데이터를 결합한 데이터마이닝 프로젝트</p>
          <div class="cover-box">
            <p><b>핵심 키워드</b>: 네이버 지식인 증상 데이터, disease_master, symptom_classifier.pkl, 질환별 문진, 응급도 계산, 병원 추천</p>
            <p><b>GitHub</b>: ironlife827-boop/gangwon-emergency-hospital-guide</p>
          </div>
          <div class="footer"><span>Data Mining Team Report</span><span>표지</span></div>
        </section>
        """
    )

    pages.append(
        """
        <section class="page">
          <h1>목차</h1>
          <div class="toc-line"><span>1. 목표정의</span><span>1</span></div>
          <div class="toc-line"><span>1.1. 타깃층 및 선정 이유</span><span>1</span></div>
          <div class="toc-line"><span>2. 데이터 수집 & 정제</span><span>3</span></div>
          <div class="toc-line"><span>2.1. 데이터 소스와 수집 방법</span><span>3</span></div>
          <div class="toc-line"><span>2.2. 정제와 라벨 통합</span><span>4</span></div>
          <div class="toc-line"><span>3. 데이터 탐색</span><span>5</span></div>
          <div class="toc-line"><span>4. 데이터 분석</span><span>6</span></div>
          <div class="toc-line"><span>4.1. 모델 학습 및 비교</span><span>6</span></div>
          <div class="toc-line"><span>4.2. 문진·응급도·추천 로직</span><span>7</span></div>
          <div class="toc-line"><span>5. 데이터 활용 & 결과 보고</span><span>9</span></div>
          <div class="toc-line"><span>부록 A. WBS 및 역할 분담</span><span>부록</span></div>
          <div class="toc-line"><span>부록 B. GitHub 파일 구조</span><span>부록</span></div>
          <div class="toc-line"><span>부록 C. 실행 검증 결과</span><span>부록</span></div>
          <div class="toc-line"><span>참고문헌</span><span>마지막</span></div>
          <div class="footer"><span>강원도 맞춤형 응급 및 상시 병원 안내 시스템</span><span>목차</span></div>
        </section>
        """
    )

    page(
        "1. 목표정의",
        f"""
        <p>본 프로젝트는 강원도 지역 사용자가 자연어로 증상을 입력하면 의심 질환, 추천 진료과, 응급도, 주변 병원을 안내하는 웹 서비스를 구현하는 것을 목표로 한다. 단순 병원 검색이 아니라 <b>증상 → 질환 후보 → 질환별 문진 → 위험도 계산 → 병원 추천</b>을 하나의 흐름으로 연결한다.</p>
        <h3>1.1. 타깃층 및 선정 이유</h3>
        <p>타깃층은 야간·주말 또는 낯선 지역에서 병원 선택이 어려운 강원도 거주자와 방문자이다. 응급 상황에서는 사용자가 자신의 증상은 설명할 수 있어도 진료과와 병원 선택은 어렵다. 공공 응급의료 API가 실시간 가용병상 정보를 제공한다는 점은 병원 추천에 활용할 수 있는 중요한 근거가 된다[3].</p>
        <p>기존 병원 검색 서비스는 사용자가 이미 “어느 진료과를 갈지” 알고 있다는 전제에서 출발하는 경우가 많다. 그러나 실제 상황에서는 “가슴이 답답하고 숨이 차다”, “오른쪽 아랫배가 아프다”, “목이 아프고 콧물이 난다”처럼 증상 중심으로 판단이 시작된다. 본 프로젝트는 이 간극을 줄이기 위해 자연어 증상 분류 모델을 핵심 축으로 두었다.</p>
        <div class="analysis-box"><b>문제 유형 선정 근거</b><br>입력 데이터는 자연어 문장이고 출력은 증상군, 진료과, 의심 질환이므로 다중 분류 문제로 정의했다. 이후 응급도는 별도 risk score 계산 문제로 분리하여, 질환 예측 모델이 모든 판단을 독점하지 않도록 설계했다.</div>
        <div class="grid3">
          <div class="card"><div class="metric">3,499</div><b>증상 사례</b><p class="small">자연어 증상 학습 데이터</p></div>
          <div class="card"><div class="metric">149</div><b>질환 마스터</b><p class="small">질환명·별칭·진료과 통합</p></div>
          <div class="card"><div class="metric">1,994</div><b>병원 정보</b><p class="small">상시/응급 병원 추천 기반</p></div>
        </div>
        <p class="note">본 시스템은 의료 진단을 대체하지 않으며, 응급도와 병원 선택을 돕는 의사결정 보조 시스템으로 정의하였다.</p>
        """,
        "1",
    )

    page(
        "1.2. 시스템 개요",
        f"""
        <p>사용자는 증상을 입력하고 위치를 설정한다. 백엔드는 학습된 <b>symptom_classifier.pkl</b>을 우선 사용하여 증상군, 진료과, 의심 질환 TOP3를 예측한다. 이후 disease_question_map에서 질환별 질문을 랭킹하여 최소 1~4개의 문진만 제시한다.</p>
        {img_tag('team_report_assets/system_pipeline_diagram.png', '그림 1. 전체 시스템 파이프라인')}
        <p>응급도는 질환 예측 모델이 아니라 red flag와 문진 답변의 risk_score로 별도 계산한다. 이 구조는 질환 판단 데이터와 응급도 보조 데이터를 분리하기 위한 설계이다.</p>
        <p>초기 구현에서는 응급 룰 데이터가 질환 판단에도 영향을 주면서, “숨쉬기 힘들다”라는 키워드만 보고 익수처럼 전혀 다른 상황을 의심하는 문제가 있었다. 이를 개선하기 위해 질환 판단은 네이버 지식인 기반 증상 모델과 disease_master 중심으로 수행하고, triage_rule_dataset은 fallback 및 위험도 보조 용도로 제한했다.</p>
        <p>또한 사용자 입력에 이미 포함된 정보는 다시 질문하지 않도록 positive_keywords 기반 중복 제거를 적용했다. 예를 들어 사용자가 이미 “입술이 붓고 숨쉬기 힘들다”고 입력했다면, 해당 정보를 반복 확인하는 질문보다 노출 음식, 전신 두드러기, 의식 저하처럼 부족한 정보 확인 질문을 우선한다.</p>
        <div class="analysis-box"><b>시스템 완성도 관점</b><br>입력, 분석, 문진, 최종 응급도, 병원 추천이 모두 API와 UI로 연결되어 있어 단일 모델 실험이 아니라 실제 사용 가능한 웹 서비스 흐름으로 구현했다.</div>
        """,
        "2",
    )

    page(
        "2. 데이터 수집 & 정제",
        f"""
        <h3>2.1. 데이터 소스와 수집 방법</h3>
        <p>데이터는 네이버 지식인 증상 사례, 질환 마스터, 질환별 문진 질문, 응급 문진 룰, 병원 기본정보, 응급 병상 데이터로 구성했다. 네이버 지식인은 실제 사용자들이 작성하는 자연어 증상 표현을 확보하기 위해 사용했다.</p>
        {table_html(['데이터', '규모', '활용 목적'], data_rows)}
        <p>서울아산병원 질환백과는 원문을 학습 데이터로 그대로 넣기보다 질환명, 증상, 관련 진료과 체계를 보강하는 기준으로 사용했다[5]. 카카오 로컬 API는 위치 검색, 카카오모빌리티 길찾기 API는 ETA 계산, 공공데이터 EGEN API는 응급실 병상 조회에 활용했다[1]-[4].</p>
        <p>네이버 지식인 데이터는 “사용자가 실제로 어떤 말투로 증상을 쓰는가”를 반영하기에 적합하다. 반면 병원 추천에는 사용자 표현 데이터만으로는 부족하므로, 병원 기본정보와 병상 데이터를 별도로 결합했다. 즉, 하나의 데이터셋에 모든 역할을 맡기지 않고, 각 데이터가 가장 잘 설명할 수 있는 문제에만 사용했다.</p>
        <p>수집 이후에는 원문(raw_text), 정제문(cleaned_text), 증상 키워드(symptom_keywords), 증상군(symptom_group), 진료과(department), 의심 질환(suspected_disease), 응급도(severity_level)를 유지했다. 이 컬럼 구조는 학습, 평가, 서비스 추론에서 동일하게 사용되도록 설계했다.</p>
        <div class="analysis-box"><b>데이터 활용 원칙</b><br>자연어 증상 데이터는 질환 예측에, 응급 문진 데이터는 위험도 계산에, 병원/병상 데이터는 추천에 사용했다. 역할이 다른 데이터를 섞어 쓰면 모델이 키워드 하나에 과잉 반응할 수 있어 데이터 역할을 명확히 분리했다.</div>
        """,
        "3",
    )

    page(
        "2.2. 정제와 라벨 통합",
        f"""
        <p>정제 과정에서는 비의료성 텍스트, 동물 관련 질문, 꿈 해몽, 법률 상담 등 증상 분류 목적과 맞지 않는 사례를 제거했다. 이후 cleaned_text와 symptom_keywords를 입력 피처로 구성하고, symptom_group, department, suspected_disease를 예측 대상으로 구성했다.</p>
        {img_tag('team_report_assets/data_role_diagram.png', '그림 2. 데이터별 역할 분리')}
        <p>특히 같은 질환이 여러 이름으로 나타나는 문제를 줄이기 위해 <b>disease_master.csv</b>를 만들고 disease_id 기준으로 통합했다. 예를 들어 ‘심근경색’, ‘급성 심근경색’, ‘AMI’는 같은 disease_id로 연결한다. 이 매핑 구조는 부록 B의 GitHub 파일 구조와 함께 확인할 수 있다.</p>
        <p>라벨 통합은 모델 성능뿐 아니라 문진과 병원 추천에도 영향을 준다. 모델이 “급성 심근경색”을 예측했는데 질문 DB에는 “심근경색”으로 저장되어 있으면 질환 전용 질문을 찾지 못한다. 따라서 disease_master는 단순 사전이 아니라 모델, 문진, 응급도, 병원 추천을 연결하는 공통 키 역할을 한다.</p>
        <p>정제 기준은 분석 결과에 직접 영향을 주기 때문에 최대한 명시적으로 관리했다. 예를 들어 “강아지가 토한다”, “꿈에서 피를 봤다”, “교통사고 합의 문의”는 텍스트에 의료 단어가 포함되어도 사람 환자의 증상 분류와 맞지 않으므로 제거 대상이다. 반대로 짧은 표현이라도 “설사 6번 복통”, “오른쪽 아랫배 통증”처럼 의료적 판단에 필요한 표현은 유지했다.</p>
        <div class="analysis-box"><b>정제 후 효과</b><br>mapped CSV 기준 unknown disease_id가 0건이 되도록 점검했고, 서비스가 읽는 CSV는 모두 disease_id 기준으로 연결되도록 구성했다.</div>
        """,
        "4",
    )

    page(
        "3. 데이터 탐색",
        f"""
        <p>데이터 탐색에서는 증상군, 진료과, 질환 라벨 분포를 확인했다. 아래 그래프는 상위 10개 증상군 분포를 나타낸다. toxic, trauma, respiratory, cardio, abdominal 등 응급성과 일반 질환이 함께 존재한다.</p>
        {img_tag('team_report_assets/symptom_group_distribution.png', '그림 3. 증상군별 데이터 분포 TOP10')}
        <p>이 분포는 모델 선정의 근거가 된다. 질환명 라벨 수가 많고 한국어 문장 표현이 다양하므로 단순 키워드 매칭보다 문자 n-gram 기반 TF-IDF 모델이 유리하다고 판단했다. 또한 데이터 편중이 존재하므로 baseline 모델과 비교해 실제 학습 효과를 검증했다.</p>
        <p>탐색 결과 일부 증상군과 질환은 데이터가 많고, 일부 일반 질환은 상대적으로 적었다. 이 때문에 단순 정확도만 보면 다수 클래스에 유리한 모델을 선택할 위험이 있다. 따라서 accuracy와 함께 macro F1, weighted F1을 함께 확인했다. macro F1은 각 클래스를 균등하게 반영하므로 소수 질환에 대한 성능 저하를 파악하는 데 중요하다.</p>
        <p>또한 진료과 분포를 보면 응급의학과가 가장 많지만, 실제 서비스에서는 감기, 편도염, 장염처럼 비응급 상시 진료가 필요한 증상도 포함해야 한다. 따라서 응급실만 추천하는 시스템이 아니라, 응급도 3~5단계에서는 주변 상시 병원도 추천하도록 설계 방향을 수정했다.</p>
        <div class="analysis-box"><b>탐색 인사이트</b><br>데이터 분포 확인 결과, 질환 예측 모델은 자연어 표현의 다양성을 처리해야 하고, 추천 시스템은 응급 병원과 상시 병원을 함께 다룰 필요가 있었다.</div>
        """,
        "5",
    )

    page(
        "4. 데이터 분석",
        f"""
        <h3>4.1. 모델 학습 및 비교</h3>
        <p>모델은 자연어 증상 문장을 입력받아 symptom_group, department, suspected_disease를 예측한다. 학습 과정에서는 majority baseline, word TF-IDF + Logistic Regression, char TF-IDF + Logistic Regression, char TF-IDF + Linear SVC를 비교했다.</p>
        {img_tag('team_report_assets/model_comparison_accuracy.png', '그림 4. 모델별 정확도 비교')}
        {table_html(['Target', 'Best model', 'Accuracy', 'Macro F1', 'Classes'], best_rows)}
        <p>질환명 예측은 121개 클래스를 대상으로 하며, 단순 baseline 대비 TF-IDF 기반 모델에서 큰 성능 향상을 보였다. 자세한 분류 리포트는 부록 C 및 <code>docs/symptom_classifier_evaluation.md</code>에 정리했다.</p>
        <p>모델 비교는 “하나의 모델만 사용했다”는 한계를 줄이기 위해 수행했다. 다수 클래스 baseline 대비 TF-IDF 계열 모델의 성능이 크게 높아, 모델이 실제 자연어 증상 표현을 학습했음을 확인했다. symptom_group과 department는 char TF-IDF + Linear SVC가 안정적이었고, suspected_disease는 word TF-IDF Logistic Regression도 높은 성능을 보였다.</p>
        <div class="analysis-box"><b>해석 기준</b><br>높은 수치가 의료적 완벽성을 의미하지는 않는다. 따라서 서비스에서는 TOP1만 사용하지 않고 TOP3 후보, 질환별 문진, red flag 보정을 함께 사용한다.</div>
        """,
        "6",
    )

    page(
        "4.2. 모델 학습 코드",
        f"""
        <p>모델 학습 코드는 <code>data_pipeline/symptom_model/train_symptom_classifier.py</code>에 위치한다. 아래 코드는 char n-gram TF-IDF로 한국어 증상 문장의 부분 문자열 패턴을 반영하고, LinearSVC 분류기로 라벨을 예측하는 핵심 구조이다.</p>
        {img_tag('team_report_assets/code_model_training.png', '그림 5. 모델 학습 코드 스니펫')}
        <p>이 방식은 띄어쓰기 오류, 조사 변화, 짧은 증상 표현이 많은 한국어 사용자 입력에서 단어 단위보다 안정적으로 작동한다. 모델 결과는 진단이 아니라 의심 질환 후보로 사용되며, 이후 문진과 응급도 계산으로 보정된다.</p>
        <p>학습 데이터는 cleaned_text와 symptom_keywords를 결합해 입력 피처로 사용한다. cleaned_text는 사용자의 원문에서 불필요한 표현을 줄인 문장이고, symptom_keywords는 통증 부위나 주요 증상 단어를 보강한 필드이다. 두 정보를 함께 사용하면 “목이 아프고 콧물”처럼 짧은 문장에서도 질환군을 더 안정적으로 구분할 수 있다.</p>
        <p>학습 결과는 하나의 pkl 파일 안에 symptom_group_model, department_model, disease_model, disease_id_model, metadata 형태로 저장된다. 서비스에서는 disease_id_model을 우선 사용하여 안정적인 라벨 키를 얻고, disease_master를 통해 사용자에게 보여줄 질환명과 진료과 정보를 연결한다.</p>
        <div class="analysis-box"><b>코드 설명</b><br><code>TfidfVectorizer</code>는 문장을 수치 벡터로 바꾸고, <code>LinearSVC</code>는 해당 벡터를 라벨로 분류한다. <code>class_weight="balanced"</code>는 라벨 불균형 상황에서 소수 클래스가 완전히 무시되는 문제를 완화하기 위한 설정이다.</div>
        """,
        "7",
    )

    page(
        "4.3. 문진 및 응급도 계산",
        f"""
        <p>추가 문진은 모든 사용자에게 고정 질문을 제공하지 않는다. 모델이 예측한 disease_id와 symptom_group을 기준으로 disease_question_map 후보를 불러온 뒤, 질환 일치 점수, 증상군 일치 점수, risk_score, importance를 합산하고 이미 입력한 정보는 패널티를 적용한다.</p>
        {img_tag('team_report_assets/code_question_ranking.png', '그림 6. 문진 질문 랭킹 코드 스니펫')}
        <p>응급도는 문진 답변의 risk_score와 red flag를 기준으로 10점 만점 위험 점수를 계산한 뒤 1~5단계로 변환한다. 예를 들어 호흡곤란, 의식저하, 편마비, 흉통은 모델 신뢰도와 무관하게 위험도를 높이는 안전 장치로 작동한다.</p>
        <p>질문 선택에서 가장 큰 개선점은 symptom_group만 맞는 질문을 무작위로 섞지 않는 것이다. 예를 들어 “설사 6번 복통” 입력에는 출혈 질문보다 복부/소화기 질환 질문이 우선되어야 한다. 이를 위해 disease_id 일치 점수에 가장 큰 가중치를 두고, symptom_group은 보조 점수로만 사용했다.</p>
        <p>질문 수 역시 고정하지 않았다. 입력 문장이 짧고 모호하거나 모델 confidence가 낮으면 질문 수를 늘리고, 이미 증상이 구체적으로 작성되어 있으면 질문 수를 줄인다. 이 방식은 사용자의 피로도를 낮추면서도 응급 판단에 필요한 핵심 정보는 확보하기 위한 설계이다.</p>
        <div class="analysis-box"><b>안전성 보정</b><br>모델이 일반 질환을 예측하더라도 red flag가 감지되면 응급도를 높인다. 반대로 감기처럼 비응급 가능성이 높은 경우에는 상시 병원 추천 흐름으로 이어지도록 설계했다.</div>
        """,
        "8",
    )

    page(
        "4.4. 병원 추천 및 API 활용",
        f"""
        <p>병원 추천은 거리만 사용하지 않는다. 진료과 매칭, 응급기관 여부, 가용 병상, ETA를 함께 반영한다. 가용 병상이 0개인 병원은 가까워도 우선순위를 낮추도록 설계했다.</p>
        {img_tag('team_report_assets/code_hospital_ranking.png', '그림 7. 병원 추천 코드 스니펫')}
        <p>외부 API는 모델 판단을 대신하지 않고 위치와 실시간성을 보완한다. Kakao Local API는 주소·장소 검색, Kakao Mobility API는 경로와 이동 시간 계산, 공공데이터 EGEN API는 실시간 응급 병상 조회에 사용한다. API 실패 시 정적 CSV 또는 ETA 모델로 fallback한다.</p>
        <p>응급도가 높은 경우에는 응급의학과와 응급기관 여부, 가용 병상을 더 크게 반영한다. 반대로 감기, 편도염, 장염처럼 비응급 가능성이 높은 경우에는 가까운 내과, 이비인후과, 소화기내과 등 상시 병원을 추천할 수 있도록 병원 유형을 분기한다. 이 설계는 “응급 안내 시스템”이지만 모든 증상을 응급실로 보내지 않기 위한 장치이다.</p>
        <p>ETA 계산은 직선거리보다 현실적인 이동 시간을 제공하기 위한 기능이다. 사용자가 지도 검색이나 현재 위치를 통해 좌표를 설정하면, 병원 좌표와 함께 경로 URL을 생성한다. API 응답이 없거나 키가 설정되지 않은 환경에서는 학습된 eta_model 또는 거리 기반 추정값을 사용해 서비스가 멈추지 않도록 했다.</p>
        <div class="analysis-box"><b>추천 로직 해석</b><br>추천 점수는 내부 계산용으로만 사용하고 UI에는 표시하지 않는다. 사용자는 점수보다 병원명, 진료과 매칭, 예상 이동시간, 병상 여부, 지도 경로를 확인하는 것이 더 직관적이기 때문이다.</div>
        """,
        "9",
    )

    page(
        "5. 데이터 활용 & 결과 보고",
        f"""
        <p>최종 시스템은 사용자가 증상을 입력하면 문진, 분석, 병원 추천을 하나의 화면에서 제공한다. UI는 내부 추천 점수보다 사용자가 바로 이해해야 하는 응급도, 의심 질환, 진료과, 병원 정보를 중심으로 구성했다.</p>
        <div class="grid2 report-shots">
        {img_tag('team_report_assets/service_input_mock.png', '그림 8. 사용자 증상 입력 화면')}
        {img_tag('team_report_assets/service_result_mock.png', '그림 9. 분석 결과 및 병원 추천 화면')}
        </div>
        <p>사용 시나리오는 다음과 같다. 사용자가 “갑자기 한쪽 팔에 힘이 빠지고 말이 어눌해졌습니다”라고 입력하면 모델은 신경계·뇌졸중 후보를 예측하고, 뇌졸중 전용 문진을 제시한다. 이후 응급도를 높게 계산하고 응급의학과 또는 관련 응급기관을 추천한다.</p>
        <p>비응급 시나리오에서는 흐름이 다르다. “어제부터 목이 아프고 콧물이 나며 기침이 조금 있고 열은 37.5도”처럼 입력하면 감기 또는 상기도 감염 계열을 우선 의심하고, 심각한 호흡곤란이나 고열 지속 여부를 확인한 뒤 상시 병원을 추천한다. 이를 통해 응급실 과잉 추천을 줄이고 실제 사용자의 병원 선택 문제를 해결하려고 했다.</p>
        <p>최종 결과 화면에는 판단 요약도 함께 제공한다. 이 문장은 “네이버 지식인 증상 데이터 기반 학습 모델이 최종 증상을 분석했고, 응급 문진 데이터는 위험도 계산에 보조적으로 사용했다”는 구조를 사용자에게 설명한다. 즉, 결과가 단순 키워드 매칭이 아니라 데이터 기반 모델과 위험도 보정의 결합임을 보여준다.</p>
        <p class="note">실행 검증 결과 모델 로드, mapped CSV 로딩, backend 실행, smoke test, 주요 API 응답은 모두 PASS였다. 세부 결과는 부록 C에 제시하였다.</p>
        """,
        "10",
    )

    page(
        "부록 A. WBS 및 역할 분담",
        f"""
        {table_html(['단계', '작업', '산출물'], [
            ['1', '문제 정의 및 요구사항 정리', '프로젝트 목표, 평가 기준 대응'],
            ['2', '데이터 수집', '네이버 지식인 증상 사례, 병원/병상 데이터'],
            ['3', '전처리 및 라벨 통합', 'cleaned_text, disease_master, mapped CSV'],
            ['4', '모델 학습 및 평가', 'symptom_classifier.pkl, 모델 비교표'],
            ['5', '백엔드 구현', 'FastAPI, 문진/응급도/추천 서비스'],
            ['6', '프론트 구현', '증상 입력, 문진, 결과 UI'],
            ['7', '검증 및 보고서', 'validation report, 발표자료, 최종 보고서'],
        ])}
        {table_html(['역할', '담당 내용'], [
            ['데이터 담당', '수집 쿼리 설계, 정제 기준 수립, 라벨 매핑'],
            ['모델 담당', 'TF-IDF 모델 비교, 학습, 평가 리포트 작성'],
            ['백엔드 담당', '문진 선택, 응급도 계산, 병원 추천 API 구현'],
            ['프론트 담당', '사용자 입력/문진/결과 화면 구현'],
            ['검증 담당', 'smoke test, API 테스트, GitHub 구조 정리'],
        ])}
        """,
        "A",
    )

    page(
        "부록 B. GitHub 파일 구조",
        f"""
        <p>GitHub 제출 시 분석 코드, 학습 코드, 전처리 코드, 서비스 코드가 구분되도록 정리했다. 과거 실험 자료는 삭제하지 않고 archive 하위로 이동해 혼동을 줄였다.</p>
        {table_html(['폴더', '설명'], file_rows)}
        <p>실제 서비스 핵심 파일은 <code>models/symptom_classifier.pkl</code>, <code>data/disease_master.csv</code>, <code>data/processed/*_mapped.csv</code>, <code>backend/services/*.py</code>, <code>frontend/app/page.tsx</code>이다.</p>
        """,
        "B",
    )

    page(
        "부록 C. 실행 검증 결과",
        f"""
        {table_html(['검증 항목', '결과'], [
            ['모델 로드', 'PASS - symptom_classifier.pkl payload keys 확인'],
            ['disease_master 로딩', 'PASS - 149 rows, unique disease_id 확인'],
            ['mapped CSV 로딩', 'PASS - unknown disease_id 0건'],
            ['symptom_engine 실행', 'PASS - 감기/respiratory/candidates=3'],
            ['질문 선택', 'PASS - 급성 심근경색 질문 3개'],
            ['backend 실행', 'PASS - /health 응답 정상'],
            ['주요 API 응답', 'PASS - /triage/questions, /triage/analyze 정상'],
            ['smoke test', 'PASS - fail_lines=0'],
        ])}
        <p>전체 검증 리포트는 <code>reports/final_system_validation_report.md</code>에 저장했다. 프로젝트는 의사결정 보조 시스템이므로 희귀 표현, 외부 API 장애, 공공데이터 최신성은 남은 위험 요소로 관리한다.</p>
        """,
        "C",
    )

    page(
        "참고문헌",
        """
        <p>[1] Kakao Developers, “Local API Documentation,” Kakao Corp. [Online]. Available: https://developers.kakao.com/docs/ko/local/common</p>
        <p>[2] Kakao Mobility Developers, “Driving Directions API,” Kakao Mobility. [Online]. Available: https://developers.kakaomobility.com/affiliate-en/navi-api/directions.html</p>
        <p>[3] 공공데이터포털, “국립중앙의료원_전국 응급의료기관 정보 조회 서비스.” [Online]. Available: https://www.data.go.kr/data/15000563/openapi.do</p>
        <p>[4] 공공데이터포털, “국립중앙의료원_전국 병·의원 찾기 서비스.” [Online]. Available: https://www.data.go.kr/data/15000736/openapi.do</p>
        <p>[5] 서울아산병원, “질환백과 | 의료정보 | 건강정보.” [Online]. Available: https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseSubmain.do</p>
        <p>[6] scikit-learn developers, “TfidfVectorizer and LinearSVC Documentation.” [Online]. Available: https://scikit-learn.org/</p>
        <p>[7] FastAPI, “FastAPI Documentation.” [Online]. Available: https://fastapi.tiangolo.com/</p>
        """,
        "Ref.",
    )

    return f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>팀 최종 보고서</title><style>{css}</style></head><body>{''.join(pages)}</body></html>"


def write_pdf() -> bool:
    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        return False
    uri = HTML_PATH.resolve().as_uri()
    cmd = [
        str(edge),
        "--headless",
        "--disable-gpu",
        "--no-first-run",
        f"--user-data-dir={REPORTS / 'edge_pdf_profile'}",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={PDF_PATH}",
        uri,
    ]
    subprocess.run(cmd, check=False, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return PDF_PATH.exists()


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    generate_assets()
    HTML_PATH.write_text(build_html(), encoding="utf-8")
    pdf_ok = write_pdf()
    print(HTML_PATH)
    print(PDF_PATH if pdf_ok else "PDF generation skipped")


if __name__ == "__main__":
    main()
