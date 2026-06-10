from __future__ import annotations

import math
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pptx import Presentation
from pptx.util import Inches


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ASSETS = REPORTS / "presentation_assets"
VISUAL_DIR = ASSETS / "visual_slides"
PPTX_PATH = REPORTS / "gangwon_emergency_hospital_guide_presentation.pptx"
PPTX_FALLBACK_PATH = REPORTS / "gangwon_emergency_hospital_guide_presentation_visual_v2.pptx"
PPTX_UNLOCKED_PATH = REPORTS / "gangwon_emergency_hospital_guide_presentation_ai_final.pptx"
NOTES_PATH = REPORTS / "presentation_speaker_notes.md"

W, H = 1920, 1080

FONT = Path("C:/Windows/Fonts/malgun.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


def f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


NAVY = "#08142c"
NAVY2 = "#0f2344"
BLUE = "#1c6cff"
CYAN = "#00cbe8"
MINT = "#20d6a1"
RED = "#ff4d5a"
YELLOW = "#ffc247"
WHITE = "#ffffff"
BG = "#f5f8fb"
PANEL = "#ffffff"
INK = "#16233a"
MUTED = "#6b7c93"
LINE = "#d9e5ee"


def canvas(bg=BG):
    return Image.new("RGB", (W, H), bg)


def draw_text(draw, xy, text, size=42, color=INK, bold=False, anchor=None, align="left", spacing=8):
    draw.multiline_text(xy, text, font=f(size, bold), fill=color, anchor=anchor, align=align, spacing=spacing)


def text_box(draw, xy, wh, text, size=34, color=INK, bold=False, align="left", line_chars=18, spacing=8):
    x, y = xy
    lines = []
    for raw in text.split("\n"):
        if not raw:
            lines.append("")
        else:
            lines.extend(wrap(raw, width=line_chars, break_long_words=False))
    draw.multiline_text((x, y), "\n".join(lines), font=f(size, bold), fill=color, align=align, spacing=spacing)


def rounded(draw, box, r=34, fill=PANEL, outline=None, width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def shadowed_card(img, box, r=34, fill=PANEL, outline=LINE):
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    shifted = (box[0] + 10, box[1] + 14, box[2] + 10, box[3] + 14)
    sd.rounded_rectangle(shifted, radius=r, fill=(20, 40, 80, 34))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB"))
    d = ImageDraw.Draw(img)
    rounded(d, box, r, fill, outline, 2)


def pill(draw, box, text, fill=CYAN, color=NAVY, size=24):
    rounded(draw, box, r=(box[3] - box[1]) // 2, fill=fill, outline=fill)
    draw.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 2), text, font=f(size, True), fill=color, anchor="mm")


def title(draw, main, sub=None, color=INK):
    draw_text(draw, (110, 78), main, 56, color, True)
    if sub:
        draw_text(draw, (113, 154), sub, 25, MUTED, False)


def footer(draw, n):
    draw.text((1810, 1015), f"{n:02d}", font=f(20, True), fill="#a8b4c5", anchor="ra")


def arrow(draw, start, end, color=CYAN, width=8):
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head_len = max(24, width * 4)
    head_w = max(16, width * 2.4)
    base_x = x2 - ux * head_len
    base_y = y2 - uy * head_len
    draw.line([start, (base_x, base_y)], fill=color, width=width)
    pts = [
        (x2, y2),
        (base_x + px * head_w / 2, base_y + py * head_w / 2),
        (base_x - px * head_w / 2, base_y - py * head_w / 2),
    ]
    draw.polygon(pts, fill=color)


def paste_fit(img, path, box):
    src = Image.open(path).convert("RGB")
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    src.thumbnail((bw, bh), Image.LANCZOS)
    x = x1 + (bw - src.width) // 2
    y = y1 + (bh - src.height) // 2
    img.paste(src, (x, y))


def add_metric(draw, box, value, label, accent=CYAN):
    rounded(draw, box, 32, WHITE, LINE)
    x1, y1, x2, y2 = box
    draw.text(((x1 + x2) / 2, y1 + 68), value, font=f(58, True), fill=accent, anchor="mm")
    draw.text(((x1 + x2) / 2, y1 + 138), label, font=f(24, True), fill=MUTED, anchor="mm")


def draw_check(draw, x, y, text, color=CYAN, size=30):
    draw.ellipse((x, y + 7, x + 24, y + 31), fill=color)
    draw.text((x + 42, y), text, font=f(size, True), fill=INK)


def draw_gangwon_map(draw, box):
    x1, y1, x2, y2 = box
    scale = min((x2 - x1) / 720, (y2 - y1) / 660)
    ox = x1 + ((x2 - x1) - 720 * scale) / 2
    oy = y1 + ((y2 - y1) - 660 * scale) / 2

    def p(dx, dy):
        return (ox + dx * scale, oy + dy * scale)

    pts = [
        p(210, 30), p(520, 80), p(650, 240),
        p(590, 470), p(405, 620), p(230, 560),
        p(120, 410), p(60, 210),
    ]
    draw.polygon(pts, fill="#eafcff")
    draw.line(pts + [pts[0]], fill=CYAN, width=5, joint="curve")
    vulnerable = [
        [p(155, 170), p(335, 175), p(355, 335), p(170, 355)],
        [p(365, 310), p(555, 295), p(560, 500), p(360, 485)],
        [p(115, 405), p(300, 420), p(275, 570), p(135, 545)],
    ]
    for zone in vulnerable:
        draw.polygon(zone, fill="#ffd76b")
        draw.line(zone + [zone[0]], fill="#e8a900", width=3, joint="curve")
    sites = [
        (37.88, 127.74), (37.75, 128.90), (38.20, 128.57), (37.34, 127.95),
        (37.52, 129.11), (37.16, 128.98), (38.11, 127.99), (37.69, 127.89),
        (37.45, 128.45), (38.07, 128.17), (37.27, 128.47), (37.84, 128.89),
    ]
    min_lat, max_lat = 37.0, 38.35
    min_lon, max_lon = 127.55, 129.30
    for lat, lon in sites:
        sx, sy = p(
            110 + (lon - min_lon) / (max_lon - min_lon) * 500,
            560 - (lat - min_lat) / (max_lat - min_lat) * 480,
        )
        r = 12 * scale
        draw.ellipse((sx - r, sy - r, sx + r, sy + r), fill=RED, outline=WHITE, width=max(2, int(4 * scale)))


def draw_bar_chart(draw, origin, size, rows, highlight_label):
    x, y = origin
    w, h = size
    max_v = max(v for _, v in rows)
    step = h / len(rows)
    for i, (label, value) in enumerate(rows):
        yy = y + i * step + 18
        color = MINT if label == highlight_label else "#cfe0ee"
        draw.text((x, yy + 20), label, font=f(25, True), fill=INK, anchor="lm")
        bw = int((value / max_v) * (w - 360))
        draw.rounded_rectangle((x + 300, yy, x + 300 + bw, yy + 42), radius=18, fill=color)
        draw.text((x + 320 + bw, yy + 21), f"{value * 100:.1f}%", font=f(23, True), fill=NAVY, anchor="lm")


def slide_01():
    img = canvas(NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=NAVY)
    d.ellipse((1280, -240, 2180, 660), fill="#12345f")
    d.ellipse((1370, -140, 2070, 560), fill="#0bbbd833")
    pill(d, (110, 94, 430, 150), "DATA MINING PROJECT", CYAN, NAVY, 25)
    draw_text(d, (112, 250), "강원도 맞춤형\nAI 응급도 판단 및\n병원 추천 시스템", 70, WHITE, True, spacing=16)
    draw_text(d, (118, 600), "증상 기반 질병군 · 진료과 · ETA · 병원 추천 의사결정 지원", 32, "#c9e8f0", False)
    shadowed_card(img, (1060, 250, 1745, 760), 44, NAVY2, "#24466d")
    d.text((1405, 340), "AI Decision Flow", font=f(38, True), fill=CYAN, anchor="mm")
    flow = ["증상 입력", "응급도 판단", "질병군 추론", "ETA 기반 추천"]
    for i, item in enumerate(flow):
        y = 430 + i * 72
        d.rounded_rectangle((1180, y - 24, 1630, y + 30), radius=24, fill="#102b54", outline="#2e527a", width=2)
        d.text((1405, y + 3), item, font=f(29, True), fill=WHITE, anchor="mm")
        if i < len(flow) - 1:
            arrow(d, (1405, y + 42), (1405, y + 66), CYAN, 5)
    footer(d, 1)
    return img


def slide_02():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "문제 정의", "증상은 자연어이고, 병원 선택은 복잡하다")
    shadowed_card(img, (110, 285, 510, 675), 36)
    shadowed_card(img, (760, 235, 1160, 725), 36, "#eafcff", CYAN)
    shadowed_card(img, (1410, 285, 1810, 675), 36)
    draw_text(d, (310, 375), "사용자", 42, INK, True, anchor="mm")
    draw_text(d, (310, 505), "“말이 어눌하고\n팔에 힘이 없어요”", 30, MUTED, False, anchor="mm", align="center")
    draw_text(d, (960, 330), "비어 있던\n중간 판단", 48, NAVY, True, anchor="mm", align="center")
    draw_text(d, (960, 515), "증상군 · 진료과\n의심 질환 · 응급도", 33, BLUE, True, anchor="mm", align="center")
    draw_text(d, (1610, 390), "결과", 42, INK, True, anchor="mm")
    draw_text(d, (1610, 515), "어디로\n가야 하는가", 33, MUTED, False, anchor="mm", align="center")
    arrow(d, (525, 480), (735, 480), CYAN)
    arrow(d, (1185, 480), (1385, 480), CYAN)
    draw_text(d, (960, 865), "목표: 증상과 병원 사이의 판단 과정을 데이터마이닝으로 구현", 40, NAVY, True, anchor="mm")
    footer(d, 2)
    return img


def slide_03():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "프로젝트 목표", "많이 묻지 않고, 위험한 증상은 놓치지 않는다")
    goals = [
        ("01", "모델 기반 예측", "증상군·진료과·질환 후보"),
        ("02", "최소 문진", "필요한 질문만 1~4개"),
        ("03", "응급도 판단", "red flag 우선 보정"),
        ("04", "병원 추천", "병상·거리·ETA 반영"),
    ]
    for i, (num, head, body) in enumerate(goals):
        x = 130 + i * 445
        shadowed_card(img, (x, 295, x + 360, 655), 38)
        d.text((x + 42, 350), num, font=f(42, True), fill=CYAN)
        d.text((x + 42, 438), head, font=f(36, True), fill=NAVY)
        text_box(d, (x + 45, 525), (280, 100), body, 27, MUTED, False, line_chars=12)
    rounded(d, (255, 800, 1665, 910), 34, NAVY, NAVY)
    d.text((960, 855), "질환 판단은 모델 중심 · 응급도 데이터는 위험도 계산 보조", font=f(39, True), fill=WHITE, anchor="mm")
    footer(d, 3)
    return img


def slide_03_region_need():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "왜 강원도 맞춤형 시스템이 필요한가?", "지역 의료 접근성 차이 때문에 단순 병원 검색으로는 부족하다")
    rounded(d, (95, 250, 820, 790), 38, WHITE, LINE)
    draw_gangwon_map(d, (145, 295, 770, 755))
    rounded(d, (180, 820, 740, 890), 24, WHITE, LINE)
    d.ellipse((220, 842, 248, 870), fill=RED, outline=WHITE, width=3)
    d.text((268, 856), "응급의료기관", font=f(24, True), fill=RED, anchor="lm")
    d.rectangle((460, 843, 492, 869), fill="#ffd76b", outline="#e8a900", width=2)
    d.text((512, 856), "의료취약권역", font=f(24, True), fill=INK, anchor="lm")
    items = [
        ("산간지역 비율이 높음", "생활권과 병원권이 일치하지 않는 경우 발생"),
        ("응급의료기관 분포 불균형", "응급실 보유 병원이 일부 도시에 집중"),
        ("단순 거리보다 ETA 중요", "직선거리 10km보다 산길 20분이 더 현실적"),
        ("병원 선택 지연 문제", "응급상황에서 잘못된 병원 선택은 시간 손실"),
    ]
    for i, (head, body) in enumerate(items):
        y = 285 + i * 145
        rounded(d, (930, y, 1765, y + 112), 28, WHITE, LINE)
        d.text((985, y + 38), head, font=f(31, True), fill=NAVY)
        d.text((985, y + 82), body, font=f(23), fill=MUTED)
    rounded(d, (910, 850, 1775, 935), 28, NAVY, NAVY)
    d.text((1342, 892), "그래서: 증상 판단 + 병원 필터링 + ETA 예측이 함께 필요", font=f(31, True), fill=WHITE, anchor="mm")
    footer(d, 4)
    return img


def slide_04():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "전체 시스템 구조", "AI 모델이 의사결정 과정의 중심에 있다")
    labels = [
        ("사용자 증상 입력", "자연어 문장"),
        ("증상 전처리", "cleaned_text + keyword"),
        ("응급도 분류 모델", "TF-IDF + Linear SVC"),
        ("질병군 예측", "symptom group / TOP3"),
        ("필요 진료과 추론", "department mapping"),
        ("병원 데이터 필터링", "진료과·응급실·병상"),
        ("ETA 예측 모델", "거리·시간·교통 보정"),
        ("최종 병원 추천", "Top3 + 경로 제공"),
    ]
    y = 260
    for i, (head, sub) in enumerate(labels):
        col = i % 4
        row = i // 4
        x = 95 + col * 455
        yy = y + row * 270
        fill = "#eafcff" if i in [2, 3, 6] else WHITE
        outline = CYAN if i in [2, 3, 6] else LINE
        rounded(d, (x, yy, x + 350, yy + 160), 30, fill, outline)
        d.text((x + 175, yy + 55), head, font=f(28, True), fill=NAVY, anchor="mm")
        d.text((x + 175, yy + 105), sub, font=f(20), fill=MUTED, anchor="mm")
        if i < len(labels) - 1:
            if col < 3:
                arrow(d, (x + 360, yy + 80), (x + 440, yy + 80), CYAN, 6)
            else:
                arrow(d, (x + 175, yy + 175), (x + 175, yy + 250), CYAN, 6)
    rounded(d, (300, 860, 1620, 940), 30, NAVY, NAVY)
    d.text((960, 900), "출력: 응급도 · 의심 질환 · 추천 진료과 · 병원 TOP3 · ETA", font=f(34, True), fill=WHITE, anchor="mm")
    footer(d, 5)
    return img


def slide_05():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "데이터 파이프라인", "문제정의 → 수집 → 정제 → 탐색 → 분석 → 활용")
    stages = [
        ("문제정의", "증상과 병원 사이\n판단 모델 필요"),
        ("데이터 수집", "네이버 지식인\n증상 사례"),
        ("데이터 정제", "비의료·동물·광고\n사례 제거"),
        ("데이터 탐색", "질환·증상군\n분포 확인"),
        ("분석 결과 활용", "모델·문진·추천\n서비스 연결"),
    ]
    for i, (head, sub) in enumerate(stages):
        x = 100 + i * 360
        rounded(d, (x, 300, x + 285, 595), 34, WHITE, LINE)
        pill(d, (x + 45, 335, x + 240, 385), head, CYAN if i != 4 else MINT, NAVY, 23)
        draw_text(d, (x + 142, 482), sub, 27, INK, True, anchor="mm", align="center", spacing=8)
        if i < len(stages) - 1:
            arrow(d, (x + 295, 448), (x + 350, 448), CYAN, 7)
    d.text((960, 800), "핵심: 데이터는 질환 판단용과 응급도 보조용으로 분리", font=f(42, True), fill=NAVY, anchor="mm")
    footer(d, 5)
    return img


def slide_06():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "데이터 규모 및 출처", "증상·질환·병원·교통 데이터를 결합한 데이터마이닝 시스템")
    sources = [
        ("네이버 지식인\n증상 데이터", "26,000+ 후보\n3,499 학습 반영", CYAN),
        ("질병 정보\n데이터", "500+ 질환 지식\n149 마스터 통합", MINT),
        ("병원 정보", "2,000급 병원\n상시/응급 추천", BLUE),
        ("응급의료기관\n정보", "실시간 병상 API\n응급기관 연계", RED),
        ("교통 링크\n데이터", "21,652 링크\nETA 반영 기준", YELLOW),
        ("응급 가이드라인", "문진·red flag\nrisk_score 설계", "#8e6cff"),
    ]
    for i, (head, body, color) in enumerate(sources):
        x = 105 + (i % 3) * 605
        y = 250 + (i // 3) * 285
        rounded(d, (x, y, x + 500, y + 220), 34, WHITE, LINE)
        pill(d, (x + 90, y + 30, x + 410, y + 92), head, color, WHITE if color in [RED, BLUE, "#8e6cff"] else NAVY, 21)
        draw_text(d, (x + 250, y + 155), body, 29, INK, True, anchor="mm", align="center", spacing=8)
    rounded(d, (250, 875, 1670, 965), 30, NAVY, NAVY)
    d.text((960, 920), "핵심: 증상 분류 모델 + 응급도 보정 + ETA 기반 추천 데이터를 분리해 결합", font=f(32, True), fill=WHITE, anchor="mm")
    footer(d, 6)
    return img


def slide_07():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "데이터 이해도", "많이 모은 것보다, 같은 기준으로 연결하는 것이 중요했다")
    metrics = [
        ("3,499", "증상 사례"),
        ("149", "질환 마스터"),
        ("118", "학습 disease_id"),
        ("532", "문진 질문"),
        ("0", "unmapped row"),
    ]
    for i, (v, l) in enumerate(metrics):
        add_metric(d, (95 + i * 365, 310, 385 + i * 365, 510), v, l, MINT if i == 4 else CYAN)
    rounded(d, (245, 720, 1675, 865), 40, NAVY, NAVY)
    d.text((960, 792), "disease_id로 질환 · 질문 · 응급룰 · 병원 추천 데이터를 통합", font=f(43, True), fill=WHITE, anchor="mm")
    footer(d, 7)
    return img


def slide_08():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "라벨 통합: disease_master", "같은 질환이 다른 이름으로 흔들리는 문제를 줄였다")
    shadowed_card(img, (150, 300, 770, 700), 36)
    shadowed_card(img, (1150, 300, 1770, 700), 36, "#eafcff", CYAN)
    d.text((460, 370), "Before", font=f(42, True), fill=RED, anchor="mm")
    d.text((460, 505), "심근경색\n급성 심근경색\nAMI", font=f(36, True), fill=INK, anchor="mm", align="center")
    d.text((1460, 370), "After", font=f(42, True), fill=MINT, anchor="mm")
    d.text((1460, 505), "D_CAR_004\n급성 심근경색", font=f(42, True), fill=NAVY, anchor="mm", align="center")
    arrow(d, (805, 500), (1115, 500), CYAN, 10)
    d.text((960, 820), "모델·문진·응급룰이 같은 질환을 같은 ID로 바라본다", font=f(40, True), fill=NAVY, anchor="mm")
    footer(d, 8)
    return img


def slide_09():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "서울아산병원 질환백과 활용", "의료 지식은 학습 원문이 아니라, 질환 체계 보강 기준으로 사용")
    shadowed_card(img, (140, 285, 620, 710), 38)
    shadowed_card(img, (720, 285, 1200, 710), 38, "#eafcff", CYAN)
    shadowed_card(img, (1300, 285, 1780, 710), 38)
    d.text((380, 360), "질환백과", font=f(40, True), fill=NAVY, anchor="mm")
    d.text((380, 515), "질환명\n증상\n관련 진료과", font=f(34, True), fill=MUTED, anchor="mm", align="center")
    d.text((960, 360), "활용 방식", font=f(40, True), fill=NAVY, anchor="mm")
    d.text((960, 515), "disease_master\n별칭·증상·진료과\n보강 기준", font=f(32, True), fill=BLUE, anchor="mm", align="center")
    d.text((1540, 360), "주의점", font=f(40, True), fill=NAVY, anchor="mm")
    d.text((1540, 515), "전문 원문을\n그대로 학습시키지 않음", font=f(32, True), fill=RED, anchor="mm", align="center")
    arrow(d, (635, 500), (705, 500), CYAN, 8)
    arrow(d, (1215, 500), (1285, 500), CYAN, 8)
    rounded(d, (245, 820, 1675, 930), 36, NAVY, NAVY)
    d.text((960, 875), "목적: 모델이 사용자 표현을 다루되, 질환명과 진료과 체계는 의료 지식으로 보정", font=f(34, True), fill=WHITE, anchor="mm")
    footer(d, 9)
    return img


def slide_10():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "AI 모델의 역할", "자연어 증상을 의사결정 가능한 정보로 변환")
    rounded(d, (120, 320, 520, 640), 36, WHITE, LINE)
    rounded(d, (760, 270, 1160, 690), 36, "#eafcff", CYAN)
    rounded(d, (1400, 320, 1800, 640), 36, WHITE, LINE)
    d.text((320, 395), "입력", font=f(38, True), fill=NAVY, anchor="mm")
    d.text((320, 515), "자연어\n증상 문장", font=f(34, True), fill=MUTED, anchor="mm", align="center")
    d.text((960, 370), "symptom_classifier.pkl", font=f(34, True), fill=NAVY, anchor="mm")
    d.text((960, 500), "char TF-IDF\n+ 분류 모델\n+ disease_id", font=f(32, True), fill=BLUE, anchor="mm", align="center")
    d.text((1600, 395), "출력", font=f(38, True), fill=NAVY, anchor="mm")
    d.text((1600, 515), "증상군\n진료과\n질환 TOP3", font=f(33, True), fill=MUTED, anchor="mm", align="center")
    arrow(d, (540, 480), (740, 480), CYAN, 8)
    arrow(d, (1180, 480), (1380, 480), CYAN, 8)
    d.text((960, 820), "AI 출력은 최종 진단이 아니라 문진·응급도·추천을 시작하는 핵심 후보", font=f(34, True), fill=NAVY, anchor="mm")
    footer(d, 10)
    return img


def slide_10_emergency_model():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "응급도 판단 모델", "사용자 증상을 1~5단계 응급도 후보로 분류")
    steps = [
        ("입력", "사용자 증상"),
        ("전처리", "cleaned_text\nsymptom_keywords"),
        ("벡터화", "Char TF-IDF"),
        ("분류", "Linear SVC"),
        ("출력", "응급도 1~5"),
    ]
    for i, (head, body) in enumerate(steps):
        x = 105 + i * 360
        fill = "#eafcff" if i in [2, 3] else WHITE
        rounded(d, (x, 360, x + 280, 570), 34, fill, CYAN if i in [2, 3] else LINE)
        d.text((x + 140, 425), head, font=f(34, True), fill=NAVY, anchor="mm")
        d.text((x + 140, 500), body, font=f(27, True), fill=BLUE if i in [2, 3] else MUTED, anchor="mm", align="center")
        if i < len(steps) - 1:
            arrow(d, (x + 292, 465), (x + 350, 465), CYAN, 7)
    rounded(d, (260, 760, 1660, 880), 34, NAVY, NAVY)
    d.text((960, 820), "실서비스에서는 red flag와 문진 risk_score로 안전 보정", font=f(42, True), fill=WHITE, anchor="mm")
    footer(d, 11)
    return img


def slide_10_model_comparison():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "모델 성능 비교", "응급도 라벨 기준 실제 실험 결과")
    rows = [
        ("Naive Bayes", 0.6886),
        ("Logistic Regression", 0.9557),
        ("Random Forest", 0.9329),
        ("Linear SVC", 0.9743),
    ]
    draw_bar_chart(d, (250, 300), (1300, 420), rows, "Linear SVC")
    rounded(d, (310, 790, 1610, 910), 34, "#eafcff", CYAN)
    d.text((960, 835), "최종 선택: Linear SVC 97.43% · Macro F1 98.33%", font=f(42, True), fill=NAVY, anchor="mm")
    d.text((960, 885), "평가 기준: naver_kin_symptom_cases_mapped.csv severity_level stratified split", font=f(22), fill=MUTED, anchor="mm")
    footer(d, 12)
    return img


def slide_11():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "추가 문진", "질문을 많이 하는 것이 아니라, 필요한 질문만 고른다")
    rounded(d, (155, 285, 1765, 515), 44, NAVY, NAVY)
    d.text((960, 398), "질환 일치 + 증상군 일치 + 위험도 + 중요도 - 이미 말한 정보", font=f(42, True), fill=WHITE, anchor="mm")
    components = [("질환 전용", CYAN), ("위험도 반영", YELLOW), ("중복 제외", RED), ("Top 1~4", MINT)]
    for i, (txt, color) in enumerate(components):
        pill(d, (305 + i * 360, 670, 585 + i * 360, 735), txt, color, NAVY if color != RED else WHITE, 30)
    d.text((960, 875), "질문은 새로 생성하지 않고 disease_question_map 후보 중에서 랭킹", font=f(35, True), fill=NAVY, anchor="mm")
    footer(d, 11)
    return img


def slide_12():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "병원 추천 의사결정 로직", "단순 거리순 추천이 아니다")
    steps = [
        "응급도 판단", "질병군 예측", "진료과 추론", "병원 유형 필터링",
        "응급실 여부 확인", "ETA 계산", "Top3 추천",
    ]
    for i, step in enumerate(steps):
        x = 135 + i * 245
        y = 405
        color = RED if i == 0 else MINT if i in [1, 2] else CYAN if i >= 5 else YELLOW
        rounded(d, (x, y, x + 190, y + 145), 30, WHITE, LINE)
        pill(d, (x + 25, y + 28, x + 165, y + 78), f"{i+1}", color, WHITE if color == RED else NAVY, 28)
        d.text((x + 95, y + 112), step, font=f(23, True), fill=NAVY, anchor="mm")
        if i < len(steps) - 1:
            arrow(d, (x + 200, y + 72), (x + 235, y + 72), CYAN, 6)
    rounded(d, (250, 760, 1670, 905), 36, NAVY, NAVY)
    d.text((960, 815), "거리 + 진료과 + 응급실 + 병상 + ETA를 함께 반영", font=f(43, True), fill=WHITE, anchor="mm")
    d.text((960, 870), "가용 병상 0개 병원은 가까워도 추천 우선순위 하락", font=f(29, True), fill="#d7f7ff", anchor="mm")
    footer(d, 12)
    return img


def slide_12_eta_model():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "ETA 예측 모델", "강원도에서는 직선거리보다 예상 도착 시간이 중요하다")
    features = [
        "사용자 위치", "병원 위치", "거리", "시간대", "요일", "날씨", "강원도 교통 데이터",
    ]
    for i, feat in enumerate(features):
        x = 140 + (i % 4) * 410
        y = 290 + (i // 4) * 150
        rounded(d, (x, y, x + 300, y + 85), 25, WHITE, LINE)
        d.text((x + 150, y + 43), feat, font=f(27, True), fill=NAVY, anchor="mm")
    arrow(d, (960, 580), (960, 665), CYAN, 8)
    rounded(d, (640, 670, 1280, 790), 36, "#eafcff", CYAN)
    d.text((960, 730), "ETA 예측 모델", font=f(42, True), fill=NAVY, anchor="mm")
    arrow(d, (960, 805), (960, 865), CYAN, 8)
    rounded(d, (565, 870, 1355, 955), 32, NAVY, NAVY)
    d.text((960, 913), "예상 도착 시간 → 병원 추천 점수에 반영", font=f(34, True), fill=WHITE, anchor="mm")
    footer(d, 13)
    return img


def slide_13():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "사용한 API", "외부 API는 판단 보조와 실시간성 확보에 사용")
    apis = [
        ("Kakao Local API", "주소/장소 검색\n좌표 설정", CYAN),
        ("Kakao Mobility API", "자동차 경로\n시간·거리 보정", MINT),
        ("공공데이터 EGEN API", "응급실 가용 병상\n실시간 조회", RED),
        ("FastAPI Backend", "문진·분석·추천\n서비스 API", BLUE),
    ]
    for i, (head, body, color) in enumerate(apis):
        x = 135 + i * 445
        rounded(d, (x, 300, x + 360, 650), 38, WHITE, LINE)
        pill(d, (x + 38, 355, x + 322, 415), head, color, WHITE if color in [RED, BLUE] else NAVY, 22)
        d.text((x + 180, 535), body, font=f(31, True), fill=INK, anchor="mm", align="center")
    rounded(d, (250, 800, 1670, 920), 36, NAVY, NAVY)
    d.text((960, 860), "API 실패 시 정적 CSV 또는 ETA 모델로 fallback", font=f(42, True), fill=WHITE, anchor="mm")
    footer(d, 13)
    return img


def slide_14():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "실제 서비스 화면", "증상 입력 → 추가 질문 → 추천 결과 3단계 흐름")
    panels = [
        ("1단계", "증상 입력", "갑자기 한쪽 팔에 힘이 빠지고\n말이 어눌해졌습니다.", CYAN),
        ("2단계", "추가 질문 생성", "얼굴 한쪽이 처지나요?\n말이 잘 나오지 않나요?", YELLOW),
        ("3단계", "추천 결과", "응급도 1 · 뇌졸중 의심\n응급실 보유 병원 TOP3 · ETA", MINT),
    ]
    for i, (step, head, body, color) in enumerate(panels):
        x = 105 + i * 605
        rounded(d, (x, 270, x + 500, 780), 38, NAVY if i == 2 else WHITE, color)
        pill(d, (x + 50, 315, x + 210, 370), step, color, NAVY if color != RED else WHITE, 24)
        d.text((x + 250, 445), head, font=f(39, True), fill=WHITE if i == 2 else NAVY, anchor="mm")
        d.multiline_text((x + 250, 575), body, font=f(29, True), fill="#d7f7ff" if i == 2 else INK, anchor="mm", align="center", spacing=10)
    rounded(d, (300, 870, 1620, 955), 30, "#eafcff", CYAN)
    d.text((960, 913), "최종 화면에는 응급도 · 의심 질환 · 추천 병원 TOP3 · ETA가 함께 표시", font=f(32, True), fill=NAVY, anchor="mm")
    footer(d, 14)
    return img


def slide_14_scenario_validation():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "실제 시나리오 검증", "응급 환자와 비응급 환자의 추천 흐름이 달라진다")
    scenarios = [
        ("사례 1", "갑자기 한쪽 팔에 힘이 안 들어가고\n말이 어눌함", "뇌졸중 의심\n응급도 1", "응급실 보유 병원\nETA 기반 추천", RED),
        ("사례 2", "기침과 미열이\n2일째 지속", "호흡기 질환\n응급도 4", "내과 진료 가능\n상시 병원 추천", CYAN),
    ]
    for i, (case, inp, pred, rec, color) in enumerate(scenarios):
        x = 135 + i * 845
        rounded(d, (x, 285, x + 755, 780), 40, WHITE, color)
        pill(d, (x + 45, 330, x + 220, 390), case, color, WHITE if color == RED else NAVY, 26)
        d.text((x + 70, 465), "입력", font=f(25, True), fill=MUTED)
        d.multiline_text((x + 180, 455), inp, font=f(28, True), fill=INK, spacing=7)
        d.text((x + 70, 595), "예측", font=f(25, True), fill=MUTED)
        d.multiline_text((x + 180, 585), pred, font=f(30, True), fill=color, spacing=7)
        d.text((x + 430, 595), "추천", font=f(25, True), fill=MUTED)
        d.multiline_text((x + 535, 585), rec, font=f(28, True), fill=NAVY, spacing=7)
    rounded(d, (295, 860, 1625, 945), 30, NAVY, NAVY)
    d.text((960, 902), "같은 병원 검색이 아니라, 증상과 응급도에 따라 병원 유형이 달라진다", font=f(33, True), fill=WHITE, anchor="mm")
    footer(d, 15)
    return img


def slide_15():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "실행 검증", "정적 설명이 아니라 실제 실행으로 확인했다")
    add_metric(d, (220, 330, 560, 560), "21", "검증 항목 PASS", MINT)
    add_metric(d, (625, 330, 965, 560), "0", "FAIL", MINT)
    add_metric(d, (1030, 330, 1370, 560), "3", "주요 API 확인", CYAN)
    add_metric(d, (1435, 330, 1775, 560), "LIVE", "배포 사이트 테스트", CYAN)
    checks = "모델 로드 · disease_master · mapped CSV · backend 실행 · smoke test · /questions · /analyze"
    rounded(d, (210, 760, 1710, 875), 36, NAVY, NAVY)
    d.text((960, 817), checks, font=f(31, True), fill=WHITE, anchor="mm")
    footer(d, 15)
    return img


def slide_16():
    img = canvas(NAVY)
    d = ImageDraw.Draw(img)
    d.ellipse((-220, 650, 680, 1450), fill="#102b54")
    d.ellipse((1320, -260, 2180, 620), fill="#12345f")
    pill(d, (110, 100, 385, 158), "FINAL MESSAGE", CYAN, NAVY, 25)
    draw_text(d, (120, 255), "강원도 지역 특성을 반영한\nAI 기반 응급도 판단 및\n병원 추천 시스템", 62, WHITE, True, spacing=16)
    rounded(d, (1140, 300, 1735, 705), 42, NAVY2, "#24466d")
    bullets = ["AI 기반 응급도 판단", "증상 기반 질병군 추론", "ETA 기반 병원 추천", "병원 선택 시간 단축 기대"]
    for i, b in enumerate(bullets):
        y = 390 + i * 72
        d.ellipse((1212, y - 12, 1236, y + 12), fill=CYAN)
        d.text((1260, y), b, font=f(34, True), fill="#d7f7ff", anchor="lm")
    footer(d, 16)
    return img


SLIDES = [
    slide_01,
    slide_02,
    slide_03,
    slide_03_region_need,
    slide_04,
    slide_05,
    slide_06,
    slide_07,
    slide_08,
    slide_09,
    slide_10,
    slide_10_emergency_model,
    slide_10_model_comparison,
    slide_11,
    slide_12,
    slide_12_eta_model,
    slide_13,
    slide_14,
    slide_14_scenario_validation,
    slide_15,
    slide_16,
]

NOTES = [
    "이 프로젝트는 단순 병원 검색이 아니라 증상 기반 응급도 판단과 병원 추천을 결합한 AI 의사결정 지원 시스템입니다.",
    "사용자는 증상을 말할 수 있지만, 응급도와 진료과, 병원 선택은 어렵다는 문제에서 출발했습니다.",
    "목표는 모델 기반 예측, 최소 문진, 응급도 판단, 병원 추천 네 가지입니다.",
    "강원도는 산간지역과 의료 접근성 차이가 있어 단순 거리보다 ETA와 병원 선택 지연 문제가 중요합니다.",
    "전체 구조는 증상 전처리, 응급도 분류, 질병군 예측, 진료과 추론, 병원 필터링, ETA 예측, 최종 추천으로 구성됩니다.",
    "데이터는 수집, 정제, 탐색, 분석, 활용 단계로 구성했습니다.",
    "네이버 증상 데이터, 질병 정보, 병원 정보, 응급의료기관, 교통 링크, 응급 가이드라인을 결합했습니다.",
    "현재 서비스 데이터는 3,499건 증상 사례와 149개 질환 마스터로 통합되어 있습니다.",
    "질환명 흔들림을 줄이기 위해 disease_id를 기준으로 통합했습니다.",
    "서울아산병원 질환백과 같은 의료 지식은 질환명, 증상, 진료과 체계를 보강하는 기준으로 활용했습니다.",
    "AI 모델은 자연어 증상을 증상군, 진료과, 질환 TOP3로 바꾸는 핵심 역할을 합니다.",
    "응급도 판단 모델은 텍스트 전처리, TF-IDF, Linear SVC 흐름으로 1~5단계 후보를 예측합니다.",
    "실제 실험에서 Linear SVC가 응급도 라벨 기준 가장 높은 정확도를 보였습니다.",
    "추가 문진은 고정 질문이 아니라 질환 일치, 위험도, 중요도, 중복 패널티로 질문을 랭킹합니다.",
    "병원 추천은 단순 거리순이 아니라 응급도, 질병군, 진료과, 병원 유형, 응급실, ETA를 함께 반영합니다.",
    "ETA 예측 모델은 위치, 거리, 시간대, 요일, 날씨, 교통 데이터를 이용해 예상 도착 시간을 추천에 반영합니다.",
    "카카오 위치/길찾기 API와 공공 응급 병상 API를 사용하고 실패 시 fallback합니다.",
    "실제 서비스는 증상 입력, 추가 질문, 추천 결과 3단계로 동작합니다.",
    "시나리오 검증을 통해 응급 뇌졸중 사례는 응급실, 비응급 호흡기 사례는 상시 병원 추천으로 갈라지는 흐름을 보여줍니다.",
    "최종 검증은 21개 항목 PASS, 주요 API와 배포 사이트까지 확인했습니다.",
    "최종적으로 강원도 지역 특성을 반영한 AI 기반 응급도 판단 및 병원 추천 시스템입니다.",
]


def build_png_slides():
    VISUAL_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, maker in enumerate(SLIDES, start=1):
        img = maker()
        d = ImageDraw.Draw(img)
        d.rectangle((1740, 980, 1865, 1045), fill=img.getpixel((1800, 1000)))
        footer(d, idx)
        path = VISUAL_DIR / f"slide_{idx:02d}.png"
        img.save(path, optimize=True)
        paths.append(path)
    return paths


def build_ppt(paths):
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    for path in paths:
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(str(path), 0, 0, width=prs.slide_width, height=prs.slide_height)
    saved_primary = False
    try:
        prs.save(PPTX_PATH)
        saved_primary = True
    except PermissionError:
        pass
    if not saved_primary or PPTX_FALLBACK_PATH.exists():
        try:
            prs.save(PPTX_FALLBACK_PATH)
        except PermissionError:
            prs.save(PPTX_UNLOCKED_PATH)


def build_notes():
    lines = ["# Presentation Speaker Notes", ""]
    for idx, note in enumerate(NOTES, start=1):
        lines.append(f"## {idx}")
        lines.append(note)
        lines.append("")
    NOTES_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    REPORTS.mkdir(exist_ok=True)
    paths = build_png_slides()
    build_ppt(paths)
    build_notes()
    print(PPTX_PATH)
    if PPTX_FALLBACK_PATH.exists():
        print(PPTX_FALLBACK_PATH)
    if PPTX_UNLOCKED_PATH.exists():
        print(PPTX_UNLOCKED_PATH)
    print(VISUAL_DIR)


if __name__ == "__main__":
    main()
