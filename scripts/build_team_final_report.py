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
    save_chart_data_summary()
    save_model_comparison_chart()
    save_data_role_diagram()
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
    .page { width: 210mm; min-height: 297mm; margin: 0 auto 10px auto; padding: 16mm 15mm 14mm 15mm; background: white; page-break-after: always; position: relative; overflow: hidden; }
    .cover { background: linear-gradient(135deg, #07162d 0%, #0f2748 62%, #0cc6dc 170%); color: white; }
    h1 { font-size: 25pt; margin: 0 0 7mm 0; letter-spacing: 0; }
    h2 { font-size: 18pt; margin: 0 0 5mm 0; color: #07162d; }
    h3 { font-size: 13pt; margin: 5mm 0 2mm 0; color: #17385e; }
    p { margin: 0 0 3.2mm 0; }
    .lead { font-size: 13pt; color: #5a6a80; }
    .cover .lead { color: #d8f8ff; }
    .toc-line { display: flex; justify-content: space-between; border-bottom: 1px dotted #aab8ca; padding: 2.4mm 0; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; align-items: start; }
    .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; }
    .card { border: 1px solid #d7e2ef; border-radius: 8px; padding: 4mm; background: #f8fbff; }
    .metric { font-size: 20pt; font-weight: 700; color: #05bcd6; }
    figure { margin: 4mm 0; }
    img { width: 100%; border-radius: 6px; border: 1px solid #d6e1ef; display: block; }
    figcaption { font-size: 9.5pt; color: #607089; margin-top: 1.5mm; text-align: center; }
    table { width: 100%; border-collapse: collapse; margin: 3mm 0 5mm 0; font-size: 9.6pt; }
    th { background: #07162d; color: white; padding: 2.2mm; text-align: left; }
    td { border: 1px solid #dbe4ef; padding: 2mm; vertical-align: top; }
    ul { margin: 1mm 0 3mm 5mm; padding-left: 4mm; }
    li { margin-bottom: 1.5mm; }
    .tag { display: inline-block; border-radius: 999px; background: #eafcff; color: #08788d; font-weight: 700; padding: 1.2mm 3mm; margin: 0 1mm 1.5mm 0; }
    .note { background: #fff8df; border-left: 4px solid #ffc247; padding: 3mm; border-radius: 5px; }
    .footer { position: absolute; bottom: 7mm; left: 15mm; right: 15mm; color: #93a2b5; font-size: 9pt; display: flex; justify-content: space-between; }
    .cover-title { margin-top: 55mm; font-size: 30pt; line-height: 1.25; }
    .cover-box { margin-top: 25mm; border: 1px solid rgba(255,255,255,.35); border-radius: 10px; padding: 8mm; background: rgba(255,255,255,.08); }
    .small { font-size: 9.5pt; color: #61728a; }
    """

    pages: list[str] = []

    def page(title: str, body: str, num: str = "") -> None:
        pages.append(f'<section class="page"><h2>{title}</h2>{body}<div class="footer"><span>강원도 맞춤형 응급 및 상시 병원 안내 시스템</span><span>{num}</span></div></section>')

    pages.append(
        """
        <section class="page cover">
          <div class="cover-title">강원도 맞춤형<br>응급 및 상시 병원 안내 시스템</div>
          <p class="lead">자연어 증상 분류 모델과 실시간 병원 추천 데이터를 결합한 데이터마이닝 프로젝트</p>
          <div class="cover-box">
            <p><b>제출 형식</b>: 팀 보고서 / GitHub 코드 제출 / PDF</p>
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
        {img_tag('presentation_assets/visual_slides/slide_04.png', '그림 1. 전체 시스템 파이프라인')}
        <p>응급도는 질환 예측 모델이 아니라 red flag와 문진 답변의 risk_score로 별도 계산한다. 이 구조는 질환 판단 데이터와 응급도 보조 데이터를 분리하기 위한 설계이다.</p>
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
        """,
        "3",
    )

    page(
        "2.2. 정제와 라벨 통합",
        f"""
        <p>정제 과정에서는 비의료성 텍스트, 동물 관련 질문, 꿈 해몽, 법률 상담 등 증상 분류 목적과 맞지 않는 사례를 제거했다. 이후 cleaned_text와 symptom_keywords를 입력 피처로 구성하고, symptom_group, department, suspected_disease를 예측 대상으로 구성했다.</p>
        {img_tag('team_report_assets/data_role_diagram.png', '그림 2. 데이터별 역할 분리')}
        <p>특히 같은 질환이 여러 이름으로 나타나는 문제를 줄이기 위해 <b>disease_master.csv</b>를 만들고 disease_id 기준으로 통합했다. 예를 들어 ‘심근경색’, ‘급성 심근경색’, ‘AMI’는 같은 disease_id로 연결한다. 이 매핑 구조는 부록 B의 GitHub 파일 구조와 함께 확인할 수 있다.</p>
        """,
        "4",
    )

    page(
        "3. 데이터 탐색",
        f"""
        <p>데이터 탐색에서는 증상군, 진료과, 질환 라벨 분포를 확인했다. 아래 그래프는 상위 10개 증상군 분포를 나타낸다. toxic, trauma, respiratory, cardio, abdominal 등 응급성과 일반 질환이 함께 존재한다.</p>
        {img_tag('team_report_assets/symptom_group_distribution.png', '그림 3. 증상군별 데이터 분포 TOP10')}
        <p>이 분포는 모델 선정의 근거가 된다. 질환명 라벨 수가 많고 한국어 문장 표현이 다양하므로 단순 키워드 매칭보다 문자 n-gram 기반 TF-IDF 모델이 유리하다고 판단했다. 또한 데이터 편중이 존재하므로 baseline 모델과 비교해 실제 학습 효과를 검증했다.</p>
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
        """,
        "6",
    )

    page(
        "4.2. 모델 학습 코드",
        f"""
        <p>모델 학습 코드는 <code>data_pipeline/symptom_model/train_symptom_classifier.py</code>에 위치한다. 아래 코드는 char n-gram TF-IDF로 한국어 증상 문장의 부분 문자열 패턴을 반영하고, LinearSVC 분류기로 라벨을 예측하는 핵심 구조이다.</p>
        {img_tag('team_report_assets/code_model_training.png', '그림 5. 모델 학습 코드 스니펫')}
        <p>이 방식은 띄어쓰기 오류, 조사 변화, 짧은 증상 표현이 많은 한국어 사용자 입력에서 단어 단위보다 안정적으로 작동한다. 모델 결과는 진단이 아니라 의심 질환 후보로 사용되며, 이후 문진과 응급도 계산으로 보정된다.</p>
        """,
        "7",
    )

    page(
        "4.3. 문진 및 응급도 계산",
        f"""
        <p>추가 문진은 모든 사용자에게 고정 질문을 제공하지 않는다. 모델이 예측한 disease_id와 symptom_group을 기준으로 disease_question_map 후보를 불러온 뒤, 질환 일치 점수, 증상군 일치 점수, risk_score, importance를 합산하고 이미 입력한 정보는 패널티를 적용한다.</p>
        {img_tag('team_report_assets/code_question_ranking.png', '그림 6. 문진 질문 랭킹 코드 스니펫')}
        <p>응급도는 문진 답변의 risk_score와 red flag를 기준으로 10점 만점 위험 점수를 계산한 뒤 1~5단계로 변환한다. 예를 들어 호흡곤란, 의식저하, 편마비, 흉통은 모델 신뢰도와 무관하게 위험도를 높이는 안전 장치로 작동한다.</p>
        """,
        "8",
    )

    page(
        "4.4. 병원 추천 및 API 활용",
        f"""
        <p>병원 추천은 거리만 사용하지 않는다. 진료과 매칭, 응급기관 여부, 가용 병상, ETA를 함께 반영한다. 가용 병상이 0개인 병원은 가까워도 우선순위를 낮추도록 설계했다.</p>
        {img_tag('team_report_assets/code_hospital_ranking.png', '그림 7. 병원 추천 코드 스니펫')}
        <p>외부 API는 모델 판단을 대신하지 않고 위치와 실시간성을 보완한다. Kakao Local API는 주소·장소 검색, Kakao Mobility API는 경로와 이동 시간 계산, 공공데이터 EGEN API는 실시간 응급 병상 조회에 사용한다. API 실패 시 정적 CSV 또는 ETA 모델로 fallback한다.</p>
        """,
        "9",
    )

    page(
        "5. 데이터 활용 & 결과 보고",
        f"""
        <p>최종 시스템은 사용자가 증상을 입력하면 문진, 분석, 병원 추천을 하나의 화면에서 제공한다. UI는 내부 추천 점수보다 사용자가 바로 이해해야 하는 응급도, 의심 질환, 진료과, 병원 정보를 중심으로 구성했다.</p>
        {img_tag('presentation_assets/site_home_top.png', '그림 8. 사용자 증상 입력 화면')}
        {img_tag('presentation_assets/site_stroke_result_top.png', '그림 9. 분석 결과 및 병원 추천 화면')}
        <p>사용 시나리오는 다음과 같다. 사용자가 “갑자기 한쪽 팔에 힘이 빠지고 말이 어눌해졌습니다”라고 입력하면 모델은 신경계·뇌졸중 후보를 예측하고, 뇌졸중 전용 문진을 제시한다. 이후 응급도를 높게 계산하고 응급의학과 또는 관련 응급기관을 추천한다.</p>
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
