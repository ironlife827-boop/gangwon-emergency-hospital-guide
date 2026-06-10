from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
REPORT_DIR = ROOT / "reports"

sys.path.insert(0, str(BACKEND_DIR))


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, {"error": body}


def _get_json(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, {"error": body}


def _check(condition: bool, name: str, details: str = "") -> dict:
    return {
        "name": name,
        "status": "PASS" if condition else "FAIL",
        "details": details,
    }


def validate_model_load() -> list[dict]:
    results: list[dict] = []
    model_path = ROOT / "models" / "symptom_classifier.pkl"
    classifier = joblib.load(model_path)
    expected_keys = {"symptom_group_model", "department_model", "disease_model", "disease_id_model", "metadata"}
    results.append(_check(expected_keys.issubset(classifier.keys()), "model keys", str(classifier.keys())))

    sample = "갑자기 왼팔에 힘이 안 들어가고 말이 어눌해요"
    disease_id = str(classifier["disease_id_model"].predict([sample])[0])
    group = str(classifier["symptom_group_model"].predict([sample])[0])
    results.append(_check(bool(disease_id), "disease_id prediction", f"{sample} -> {disease_id} / {group}"))

    if hasattr(classifier["disease_id_model"], "predict_proba"):
        probabilities = classifier["disease_id_model"].predict_proba([sample])[0]
        confidence = float(max(probabilities))
        results.append(
            _check(
                0 <= confidence <= 1,
                "confidence range",
                f"top1 confidence={confidence:.4f}",
            )
        )
    return results


def validate_csv_loading() -> list[dict]:
    results: list[dict] = []
    master_path = ROOT / "data" / "disease_master.csv"
    master = pd.read_csv(master_path)
    master_required = {
        "disease_id",
        "disease_name",
        "aliases",
        "symptom_group",
        "department",
        "severity_level",
        "required_resource_code",
        "is_emergency",
        "is_model_target",
    }
    results.append(_check(master_required.issubset(master.columns), "disease_master columns"))
    results.append(_check(master["disease_id"].is_unique, "disease_master unique disease_id"))
    results.append(_check(master["disease_name"].is_unique, "disease_master unique disease_name"))

    mapped_files = [
        "naver_kin_symptom_cases_mapped.csv",
        "disease_question_map_mapped.csv",
        "triage_rule_dataset_mapped.csv",
        "emergency_disease_label_master_mapped.csv",
    ]
    for filename in mapped_files:
        path = ROOT / "data" / "processed" / filename
        df = pd.read_csv(path)
        has_mapping_cols = {"disease_id", "canonical_disease_name"}.issubset(df.columns)
        nonempty_ids = df["disease_id"].fillna("").astype(str).str.len().gt(0).all() if has_mapping_cols else False
        unknown_ids = set(df["disease_id"].astype(str)) - set(master["disease_id"].astype(str)) if has_mapping_cols else {"missing"}
        results.append(
            _check(
                has_mapping_cols and nonempty_ids and not unknown_ids,
                f"{filename} mapping",
                f"rows={len(df)}, disease_ids={df['disease_id'].nunique() if has_mapping_cols else 0}, unknown={len(unknown_ids)}",
            )
        )
    return results


def validate_backend_imports_and_services() -> list[dict]:
    results: list[dict] = []
    from services.data_loader import load_disease_master, load_disease_questions, load_naver_cases, load_triage_rules
    from services.symptom_analyzer import analyze_symptom_text
    from services.triage_service import analyze_data_driven_triage, create_data_driven_questions
    from schemas.triage import TriageAnalyzeRequest

    master = load_disease_master()
    cases = load_naver_cases()
    questions = load_disease_questions()
    rules = load_triage_rules()
    results.append(_check(not master.empty, "load_disease_master", f"rows={len(master)}"))
    results.append(_check(not cases.empty and "disease_id" in cases.columns, "load_naver_cases", f"rows={len(cases)}"))
    results.append(_check(not questions.empty and "disease_id" in questions.columns, "load_disease_questions", f"rows={len(questions)}"))
    results.append(_check(not rules.empty and "disease_id" in rules.columns, "load_triage_rules", f"rows={len(rules)}"))

    analysis = analyze_symptom_text("어제부터 목이 아프고 콧물이 나며 기침이 조금 있습니다. 열은 37.5도 정도입니다.")
    results.append(
        _check(
            analysis.get("disease_id") and len(analysis.get("disease_candidates", [])) >= 1,
            "symptom_engine current service",
            f"{analysis.get('suspected_disease')} / {analysis.get('symptom_group')} / candidates={len(analysis.get('disease_candidates', []))}",
        )
    )

    q_response = create_data_driven_questions("가슴이 답답하고 숨이 차요")
    results.append(
        _check(
            q_response.get("disease_id") and 1 <= len(q_response.get("questions", [])) <= 4,
            "question selection",
            f"{q_response.get('suspected_disease')} / questions={len(q_response.get('questions', []))}",
        )
    )

    triage = analyze_data_driven_triage(
        TriageAnalyzeRequest(symptom="목이 아프고 콧물이 나며 기침이 있습니다.", answers=[], user_lat=37.880872, user_lon=127.740228)
    )
    results.append(
        _check(
            triage.disease_id and triage.hospitals and 0 <= triage.risk_score <= 10,
            "triage analyze service",
            f"{triage.suspected_disease} / severity={triage.severity_level} / hospitals={len(triage.hospitals)}",
        )
    )
    return results


def validate_smoke_test() -> list[dict]:
    process = subprocess.run(
        [sys.executable, "-X", "utf8", "data_pipeline/symptom_model/smoke_test_triage_quality.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    failed_lines = [line for line in process.stdout.splitlines() if line.startswith("FAIL")]
    details = f"returncode={process.returncode}, fail_lines={len(failed_lines)}"
    if failed_lines:
        details += "\n" + "\n".join(failed_lines[:10])
    return [_check(process.returncode == 0 and not failed_lines, "smoke test", details)]


def validate_backend_runtime() -> list[dict]:
    port = 8017
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    results: list[dict] = []
    try:
        healthy = False
        health_body = {}
        for _ in range(30):
            if process.poll() is not None:
                break
            try:
                status, body = _get_json(f"http://127.0.0.1:{port}/api/health")
                if status == 200 and body.get("ok") is True:
                    healthy = True
                    health_body = body
                    break
            except Exception:
                pass
            time.sleep(0.5)

        results.append(_check(healthy, "backend uvicorn runtime", json.dumps(health_body, ensure_ascii=False)))
        if not healthy:
            return results

        status, questions = _post_json(
            f"http://127.0.0.1:{port}/api/triage/questions",
            {"symptom": "갑자기 왼팔에 힘이 안 들어가고 말이 어눌해요"},
        )
        results.append(
            _check(
                status == 200 and questions.get("disease_id") and "questions" in questions,
                "api /triage/questions",
                f"status={status}, disease={questions.get('suspected_disease')}, questions={len(questions.get('questions', []))}",
            )
        )

        status, analyzed = _post_json(
            f"http://127.0.0.1:{port}/api/triage/analyze",
            {
                "symptom": "목이 아프고 콧물이 나며 기침이 있습니다.",
                "answers": [],
                "user_lat": 37.880872,
                "user_lon": 127.740228,
            },
        )
        hospitals = analyzed.get("hospitals", []) if isinstance(analyzed, dict) else []
        results.append(
            _check(
                status == 200 and analyzed.get("disease_id") and hospitals,
                "api /triage/analyze",
                f"status={status}, disease={analyzed.get('suspected_disease')}, hospitals={len(hospitals)}",
            )
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    return results


def write_report(results: list[dict]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    pass_count = sum(1 for item in results if item["status"] == "PASS")
    fail_count = sum(1 for item in results if item["status"] == "FAIL")
    lines = [
        "# Final System Validation Report",
        "",
        f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Overall: {'PASS' if fail_count == 0 else 'FAIL'}",
        f"- Passed: {pass_count}",
        f"- Failed: {fail_count}",
        "",
        "## Test Results",
        "",
        "| Test | Status | Details |",
        "| --- | --- | --- |",
    ]
    for item in results:
        details = str(item.get("details", "")).replace("\n", "<br>")
        lines.append(f"| {item['name']} | {item['status']} | {details} |")

    failures = [item for item in results if item["status"] == "FAIL"]
    lines.extend(["", "## Failed Items", ""])
    if failures:
        for item in failures:
            lines.append(f"- {item['name']}: {item.get('details', '')}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Fixes Applied During Final Validation",
            "",
            "- Added repeatable final validation coverage for model loading, mapped CSV integrity, service imports, smoke tests, and live FastAPI endpoints.",
            "- Confirmed the current symptom engine is implemented by `backend/services/symptom_analyzer.py` and `backend/services/triage_service.py`; no separate `symptom_engine_v2.py` runtime file exists.",
            "",
            "## Remaining Risks",
            "",
            "- This is a decision-support demo, not a medical diagnosis system.",
            "- The model still depends on synthetic and crawled symptom text quality; rare phrasing can require fallback rules.",
            "- Realtime bed/ETA quality depends on external API keys and public data freshness.",
            "- Some legacy Korean text in source comments/README appears mojibake in the current checkout and should be explained as an encoding artifact if noticed.",
            "",
            "## Presentation Notes",
            "",
            "- Emphasize that disease prediction is TOP3 candidate support, while red flags override model confidence for safety.",
            "- Show both a non-emergency primary-care case and an emergency red-flag case.",
            "- State clearly that triage rules are used for risk scoring, not as the main disease classifier.",
        ]
    )

    (REPORT_DIR / "final_system_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    results: list[dict] = []
    for section in [
        validate_model_load,
        validate_csv_loading,
        validate_backend_imports_and_services,
        validate_smoke_test,
        validate_backend_runtime,
    ]:
        try:
            results.extend(section())
        except Exception as exc:
            results.append(_check(False, section.__name__, repr(exc)))

    write_report(results)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "PASS" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
