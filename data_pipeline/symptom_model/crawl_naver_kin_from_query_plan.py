from __future__ import annotations

import argparse
import csv
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
QUERY_PLAN_PATH = DATA_DIR / "naver_crawl_query_plan.csv"
LABEL_MASTER_PATH = DATA_DIR / "emergency_disease_label_master.csv"
BASE_CASES_PATH = DATA_DIR / "naver_kin_symptom_cases.csv"
CRAWLED_RAW_PATH = DATA_DIR / "naver_kin_expanded_crawled_raw.csv"
CRAWLED_FILTERED_PATH = DATA_DIR / "naver_kin_expanded_crawled_filtered.csv"
COMBINED_OUTPUT_PATH = DATA_DIR / "naver_kin_symptom_cases_expanded.csv"
BACKUP_PATH = DATA_DIR / "naver_kin_symptom_cases.before_expansion.csv"

CASE_COLUMNS = [
    "case_id",
    "source_url",
    "raw_text",
    "cleaned_text",
    "symptom_keywords",
    "symptom_group",
    "department",
    "suspected_disease",
    "severity_level",
]

BAD_CONTEXT_KEYWORDS = [
    "강아지",
    "고양이",
    "반려견",
    "반려묘",
    "햄스터",
    "동물병원",
    "사료",
    "꿈",
    "꿈해몽",
    "태몽",
    "법적",
    "고소",
    "소송",
    "합의금",
    "과실",
    "처벌",
    "보험금",
    "광고",
    "홍보",
    "성형",
    "쌍수",
    "키크는",
    "연애",
]

MEDICAL_HINT_KEYWORDS = [
    "아파",
    "통증",
    "증상",
    "병원",
    "응급",
    "숨",
    "열",
    "구토",
    "설사",
    "출혈",
    "피",
    "기절",
    "의식",
    "어지",
    "두통",
    "부음",
    "마비",
    "저림",
    "상처",
    "다침",
    "복통",
    "가슴",
]


def _request_text(url: str, timeout: float = 8.0) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.7,en;q=0.6",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (TimeoutError, urllib.error.HTTPError, urllib.error.URLError):
        return ""


def _strip_tags(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _clean_text(value: str) -> str:
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[\r\n\t]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -_")


def _extract_meta(html_text: str, name: str) -> str:
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.I)
        if match:
            return _clean_text(match.group(1))
    return ""


def _extract_detail_text(url: str) -> str:
    page = _request_text(url)
    if not page:
        return ""

    title = _extract_meta(page, "og:title") or _extract_meta(page, "title")
    description = _extract_meta(page, "og:description") or _extract_meta(page, "description")
    if title or description:
        return _clean_text(f"{title} {description}")

    body = _strip_tags(page)
    return body[:1200]


def _extract_search_results(search_html: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    url_pattern = re.compile(
        r'https://kin\.naver\.com/qna/detail\.naver\?[^"\'>\s]+',
        flags=re.I,
    )
    urls = []
    for raw_url in url_pattern.findall(search_html):
        url = html.unescape(raw_url)
        if url not in urls:
            urls.append(url)

    for url in urls:
        window_start = max(0, search_html.find(url) - 900)
        window_end = min(len(search_html), search_html.find(url) + 1200)
        snippet = _strip_tags(search_html[window_start:window_end])
        results.append({"source_url": url, "snippet": snippet[:1000]})

    return results


def _search_kin(query: str, page: int) -> list[dict[str, str]]:
    params = urllib.parse.urlencode({"query": query, "page": str(page)})
    url = f"https://kin.naver.com/search/list.naver?{params}"
    return _extract_search_results(_request_text(url))


def _has_bad_context(text: str) -> bool:
    normalized = text.replace(" ", "").lower()
    return any(keyword.replace(" ", "").lower() in normalized for keyword in BAD_CONTEXT_KEYWORDS)


def _has_medical_hint(text: str) -> bool:
    normalized = text.replace(" ", "").lower()
    return any(keyword.replace(" ", "").lower() in normalized for keyword in MEDICAL_HINT_KEYWORDS)


def _keyword_text(label_keywords: str, query: str) -> str:
    parts = [part.strip() for part in str(label_keywords).split(";") if part.strip()]
    query_tokens = [token.strip() for token in re.split(r"\s+", query) if len(token.strip()) >= 2]
    merged = []
    for part in parts + query_tokens:
        if part not in merged:
            merged.append(part)
    return ";".join(merged[:10])


def crawl(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    query_plan = pd.read_csv(args.query_plan)
    label_master = pd.read_csv(args.label_master)
    label_meta = label_master.set_index("suspected_disease").to_dict("index")

    rows: list[dict[str, str | int]] = []
    raw_rows: list[dict[str, str | int | bool]] = []
    seen_urls: set[str] = set()
    disease_counts: dict[str, int] = {}

    grouped_queries = query_plan.groupby("suspected_disease", sort=False)
    for disease, group in grouped_queries:
        disease_counts.setdefault(str(disease), 0)
        if args.max_labels and len(disease_counts) > args.max_labels:
            break

        meta = label_meta.get(str(disease))
        if not meta:
            continue

        query_rows = group.head(args.queries_per_label)
        for _, query_row in query_rows.iterrows():
            if disease_counts[str(disease)] >= args.target_per_label:
                break

            query = str(query_row["query"])
            for page in range(1, args.pages_per_query + 1):
                if disease_counts[str(disease)] >= args.target_per_label:
                    break

                results = _search_kin(query, page)
                time.sleep(args.delay_seconds)

                for result in results:
                    source_url = result["source_url"]
                    if source_url in seen_urls:
                        continue
                    seen_urls.add(source_url)

                    detail_text = _extract_detail_text(source_url) if args.fetch_detail else ""
                    raw_text = _clean_text(f"{result.get('snippet', '')} {detail_text}")

                    base_row = {
                        "case_id": 0,
                        "source_url": source_url,
                        "raw_text": raw_text,
                        "cleaned_text": raw_text[:1200],
                        "symptom_keywords": _keyword_text(str(meta["search_keywords"]), query),
                        "symptom_group": str(meta["symptom_group"]),
                        "department": str(meta["department"]),
                        "suspected_disease": str(disease),
                        "severity_level": int(meta["severity_level"]),
                    }

                    filter_reason = ""
                    if len(raw_text) < args.min_text_length:
                        filter_reason = "too_short"
                    elif _has_bad_context(raw_text):
                        filter_reason = "bad_context"
                    elif not _has_medical_hint(raw_text):
                        filter_reason = "no_medical_hint"

                    raw_rows.append(
                        {
                            **base_row,
                            "is_kept": not filter_reason,
                            "filter_reason": filter_reason,
                        }
                    )

                    if filter_reason:
                        continue

                    rows.append(base_row)
                    disease_counts[str(disease)] += 1

                    if disease_counts[str(disease)] >= args.target_per_label:
                        break

        print(f"{disease}: {disease_counts[str(disease)]} rows")

    raw_columns = CASE_COLUMNS + ["is_kept", "filter_reason"]
    raw_candidates = pd.DataFrame(raw_rows, columns=raw_columns)
    filtered = pd.DataFrame(rows, columns=CASE_COLUMNS)
    return raw_candidates, filtered


def combine_with_base(crawled: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    base = pd.read_csv(args.base_cases)
    for column in CASE_COLUMNS:
        if column not in base.columns:
            base[column] = ""
    base = base[CASE_COLUMNS].copy()

    combined = pd.concat([base, crawled], ignore_index=True)
    combined["cleaned_text"] = combined["cleaned_text"].fillna("").astype(str)
    combined["suspected_disease"] = combined["suspected_disease"].fillna("").astype(str)
    combined = combined.drop_duplicates(subset=["cleaned_text", "suspected_disease"], keep="first")
    combined = combined.reset_index(drop=True)
    combined["case_id"] = range(1, len(combined) + 1)
    combined["severity_level"] = pd.to_numeric(combined["severity_level"], errors="coerce").fillna(3).astype(int).clip(1, 5)
    return combined[CASE_COLUMNS]


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl Naver Knowledge iN using naver_crawl_query_plan.csv.")
    parser.add_argument("--query-plan", type=Path, default=QUERY_PLAN_PATH)
    parser.add_argument("--label-master", type=Path, default=LABEL_MASTER_PATH)
    parser.add_argument("--base-cases", type=Path, default=BASE_CASES_PATH)
    parser.add_argument("--raw-output", type=Path, default=CRAWLED_RAW_PATH)
    parser.add_argument("--filtered-output", type=Path, default=CRAWLED_FILTERED_PATH)
    parser.add_argument("--combined-output", type=Path, default=COMBINED_OUTPUT_PATH)
    parser.add_argument("--target-per-label", type=int, default=8)
    parser.add_argument("--queries-per-label", type=int, default=4)
    parser.add_argument("--pages-per-query", type=int, default=1)
    parser.add_argument("--delay-seconds", type=float, default=0.35)
    parser.add_argument("--min-text-length", type=int, default=25)
    parser.add_argument("--max-labels", type=int, default=0)
    parser.add_argument("--fetch-detail", action="store_true")
    parser.add_argument("--update-training-csv", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_candidates, crawled = crawl(args)
    write_csv(args.raw_output, raw_candidates)
    write_csv(args.filtered_output, crawled)

    combined = combine_with_base(crawled, args)
    write_csv(args.combined_output, combined)

    if args.update_training_csv:
        if args.base_cases.exists() and not BACKUP_PATH.exists():
            BACKUP_PATH.write_bytes(args.base_cases.read_bytes())
        write_csv(args.base_cases, combined)

    print("===== Crawl complete =====")
    print(f"Raw candidate rows: {len(raw_candidates)}")
    print(f"Filtered rows: {len(crawled)}")
    print(f"Combined rows: {len(combined)}")
    print(f"Raw output: {args.raw_output}")
    print(f"Combined output: {args.combined_output}")
    if args.update_training_csv:
        print(f"Updated training CSV: {args.base_cases}")


if __name__ == "__main__":
    main()
