from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
REPORT_DIR = ROOT / "reports"
sys.path.insert(0, str(BACKEND_DIR))

from schemas.triage import TriageAnalyzeRequest  # noqa: E402
from services.triage_service import analyze_data_driven_triage, create_data_driven_questions  # noqa: E402


@dataclass
class DemoInput:
    category: str
    text: str


DEMO_INPUTS = [
    DemoInput("호흡기", "목이 아프고 콧물이 나며 기침이 있습니다. 열은 37.5도 정도입니다."),
    DemoInput("호흡기", "39도 고열과 몸살, 기침이 심합니다."),
    DemoInput("호흡기", "열이 나고 기침이 있으며 냄새를 잘 못 맡겠습니다."),
    DemoInput("호흡기", "숨이 차고 쌕쌕거리는 소리가 납니다."),
    DemoInput("호흡기", "고열이 있고 기침할 때 가슴이 아픕니다."),
    DemoInput("심혈관", "가슴을 짓누르는 통증과 식은땀이 납니다."),
    DemoInput("심혈관", "운동하면 가슴이 조이는 느낌이 납니다."),
    DemoInput("심혈관", "심장이 불규칙하게 뛰고 어지럽습니다."),
    DemoInput("심혈관", "조금만 걸어도 숨이 차고 다리가 붓습니다."),
    DemoInput("신경계", "갑자기 한쪽 팔에 힘이 빠지고 말이 어눌해졌습니다."),
    DemoInput("신경계", "고열과 심한 두통이 있고 목이 뻣뻣합니다."),
    DemoInput("신경계", "작업하다가 사다리에 머리를 맞아 3초간 기절한 상태다."),
    DemoInput("신경계", "한쪽 머리가 욱신거리고 빛을 보면 심해집니다."),
    DemoInput("소화기", "설사를 6번 정도 했고 복통이 있습니다."),
    DemoInput("소화기", "오른쪽 아랫배가 심하게 아프고 걸을 때 통증이 심해집니다."),
    DemoInput("소화기", "굴을 잘못 먹고 토하고 설사를 합니다."),
    DemoInput("소화기", "속이 쓰리고 신물이 올라옵니다."),
    DemoInput("외상", "오른쪽 팔에 감전된 뒤 저리고 화끈거립니다."),
    DemoInput("외상", "넘어졌는데 팔이 붓고 움직일 수 없습니다."),
    DemoInput("외상", "칼에 손을 베였고 피가 계속 납니다."),
    DemoInput("알레르기", "벌에 쏘인 뒤 입술이 붓고 숨쉬기 힘듭니다."),
    DemoInput("알레르기", "피부에 붉은 발진이 갑자기 생기고 가렵습니다."),
    DemoInput("근골격계", "허리가 아프고 다리까지 저립니다."),
    DemoInput("근골격계", "아침에 손가락 관절이 뻣뻣합니다."),
    DemoInput("근골격계", "엄지발가락이 붓고 극심하게 아픕니다."),
    DemoInput("일반 비응급", "재채기와 콧물이 계속 납니다."),
    DemoInput("일반 비응급", "잠들기 어렵고 자주 깹니다."),
    DemoInput("일반 비응급", "아무것도 하기 싫고 계속 우울합니다."),
]


def _candidate_text(candidates: list) -> str:
    parts = []
    for candidate in candidates[:3]:
        name = getattr(candidate, "disease_name", None)
        confidence = getattr(candidate, "confidence", None)
        if isinstance(candidate, dict):
            name = candidate.get("disease_name")
            confidence = candidate.get("confidence")
        if confidence is None:
            parts.append(str(name))
        else:
            parts.append(f"{name} ({float(confidence):.2f})")
    return ", ".join(parts)


def _hospital_type(hospitals: list) -> str:
    if not hospitals:
        return "추천 없음"
    first = hospitals[0]
    is_emergency = getattr(first, "is_emergency", None)
    department = getattr(first, "department", "")
    if is_emergency == 1:
        return f"응급의료기관 / {department}"
    return f"상시병원 / {department}"


def _scenario_score(row: dict) -> float:
    confidence = row["top_confidence"]
    has_questions = 1 <= row["question_count"] <= 3
    clear_severity = row["severity_level"] in {1, 2, 4, 5}
    natural_hospital = row["hospital_type"] != "추천 없음"
    category_bonus = 0.2 if row["category"] in {"심혈관", "신경계", "알레르기", "일반 비응급", "소화기"} else 0
    return confidence * 2 + has_questions * 0.5 + clear_severity * 0.4 + natural_hospital * 0.4 + category_bonus


def main() -> int:
    rows: list[dict] = []

    for item in DEMO_INPUTS:
        questions = create_data_driven_questions(item.text)
        analysis = analyze_data_driven_triage(
            TriageAnalyzeRequest(
                symptom=item.text,
                answers=[],
                user_lat=37.880872,
                user_lon=127.740228,
            )
        )
        top_candidates = list(analysis.disease_candidates)
        top_confidence = float(top_candidates[0].confidence) if top_candidates else 0.0
        rows.append(
            {
                "category": item.category,
                "input": item.text,
                "symptom_group": analysis.symptom_group,
                "disease": analysis.suspected_disease,
                "top3": _candidate_text(top_candidates),
                "top_confidence": top_confidence,
                "severity_level": analysis.severity_level,
                "risk_score": analysis.risk_score,
                "question_count": len(questions.get("questions", [])),
                "hospital_type": _hospital_type(analysis.hospitals),
                "first_hospital": analysis.hospitals[0].hospital_name if analysis.hospitals else "",
            }
        )

    for row in rows:
        row["demo_score"] = _scenario_score(row)

    selected: list[dict] = []
    used_categories: set[str] = set()
    for row in sorted(rows, key=lambda value: value["demo_score"], reverse=True):
        if row["category"] not in used_categories or len(selected) >= 8:
            selected.append(row)
            used_categories.add(row["category"])
        if len(selected) == 10:
            break

    REPORT_DIR.mkdir(exist_ok=True)
    lines = [
        "# Demo Scenarios TOP10",
        "",
        f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Tested inputs: {len(rows)}",
        "",
        "## All Tested Inputs",
        "",
        "| Category | Input | Symptom Group | Disease TOP3 | Severity | Questions | Hospital Type |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['category']} | {row['input']} | {row['symptom_group']} | {row['top3']} | "
            f"{row['severity_level']} / risk {row['risk_score']} | {row['question_count']} | {row['hospital_type']} |"
        )

    lines.extend(["", "## Recommended TOP10", ""])
    for index, row in enumerate(selected, start=1):
        lines.extend(
            [
                f"### {index}. {row['category']} - {row['disease']}",
                "",
                f"- 추천 입력 문장: {row['input']}",
                f"- 기대 출력: `{row['symptom_group']}` / `{row['top3']}` / 응급도 `{row['severity_level']}` / 질문 `{row['question_count']}`개 / `{row['hospital_type']}`",
                f"- 첫 추천 병원: {row['first_hospital']}",
                f"- 발표 시 설명 포인트: 질환 TOP3 후보, 필요한 문진만 선택하는 흐름, 응급도에 따른 병원 유형 전환을 함께 보여주기 좋습니다.",
                "",
            ]
        )

    (REPORT_DIR / "demo_scenarios_top10.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for row in selected:
        print(f"{row['category']} | {row['input']} -> {row['disease']} / severity {row['severity_level']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
