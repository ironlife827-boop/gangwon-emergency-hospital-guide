from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


SYSTEM_PROMPT = """
너는 응급 병원 안내 시스템의 자연어 증상 구조화 보조 모듈이다.

중요 원칙:
- 진단을 확정하지 않는다.
- 응급도 최종 판단을 하지 않는다.
- 사용자의 자연어 입력에서 모델에 필요한 정형 정보를 추출한다.
- 정보가 부족하면 최대 2개까지만 추가 질문을 만든다.
- 출력은 반드시 JSON만 반환한다.

반환 JSON 형식:
{
  "normalized_symptom": "정리된 증상 문장",
  "keywords": ["증상 키워드"],
  "missing_fields": ["부족한 정보명"],
  "followup_questions": [
    {
      "question": "추가 질문",
      "options": ["예", "아니오", "잘 모르겠음"]
    }
  ]
}
"""


def _safe_json_loads(text: str) -> dict[str, Any] | None:
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def structure_symptom_with_llm(symptom: str) -> dict[str, Any] | None:
    """
    OpenAI API가 설정되어 있으면 사용자 증상을 구조화한다.
    환경변수 OPENAI_API_KEY가 없거나 호출 실패 시 None을 반환한다.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"사용자 증상 입력: {symptom}",
                },
            ],
            temperature=0.2,
            max_output_tokens=600,
        )

        data = _safe_json_loads(response.output_text)
        if not data:
            return None

        keywords = data.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        missing_fields = data.get("missing_fields", [])
        if not isinstance(missing_fields, list):
            missing_fields = []

        followup_questions = data.get("followup_questions", [])
        if not isinstance(followup_questions, list):
            followup_questions = []

        cleaned_questions = []
        for item in followup_questions[:2]:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            if not question:
                continue
            options = item.get("options", ["예", "아니오", "잘 모르겠음"])
            if not isinstance(options, list) or len(options) < 2:
                options = ["예", "아니오", "잘 모르겠음"]
            cleaned_questions.append(
                {
                    "question": question,
                    "options": [str(option) for option in options[:4]],
                }
            )

        return {
            "normalized_symptom": str(data.get("normalized_symptom", symptom)),
            "keywords": [str(keyword) for keyword in keywords[:8]],
            "missing_fields": [str(field) for field in missing_fields[:5]],
            "followup_questions": cleaned_questions,
        }

    except Exception:
        return None
