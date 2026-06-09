from __future__ import annotations

import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass


EGEN_BED_API_URL = (
    "https://apis.data.go.kr/B552657/ErmctInfoInqireService/"
    "getEmrrmRltmUsefulSckbdInfoInqire"
)
CACHE_TTL_SECONDS = 180

_cached_beds: dict[str, "RealtimeBed"] | None = None
_cached_at = 0.0


@dataclass(frozen=True)
class RealtimeBed:
    hospital_id: str
    hospital_name: str
    emergency_beds: int
    source: str
    updated_at: str


def _read_service_key() -> str:
    return (
        os.getenv("EGEN_API_KEY")
        or os.getenv("PUBLIC_DATA_SERVICE_KEY")
        or os.getenv("DATA_GO_KR_SERVICE_KEY")
        or ""
    ).strip()


def _to_int(value: str | None) -> int:
    try:
        return max(0, int(float(str(value or "0").strip())))
    except ValueError:
        return 0


def _child_text(item: ET.Element, name: str) -> str:
    child = item.find(name)
    return "" if child is None or child.text is None else child.text.strip()


def _fetch_realtime_beds() -> dict[str, RealtimeBed]:
    service_key = _read_service_key()
    if not service_key:
        return {}

    params = {
        "serviceKey": service_key,
        "STAGE1": "강원특별자치도",
        "pageNo": "1",
        "numOfRows": "100",
    }
    url = f"{EGEN_BED_API_URL}?{urllib.parse.urlencode(params, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            payload = response.read()
    except Exception:
        return {}

    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return {}

    beds: dict[str, RealtimeBed] = {}
    now_text = time.strftime("%Y-%m-%d %H:%M:%S")

    for item in root.findall(".//item"):
        hospital_id = _child_text(item, "hpid")
        hospital_name = _child_text(item, "dutyName")
        emergency_beds = _to_int(_child_text(item, "hvec"))
        updated_at = _child_text(item, "hvidate") or now_text

        if not hospital_id and not hospital_name:
            continue

        bed = RealtimeBed(
            hospital_id=hospital_id,
            hospital_name=hospital_name,
            emergency_beds=emergency_beds,
            source="egen_realtime",
            updated_at=updated_at,
        )
        if hospital_id:
            beds[hospital_id] = bed
        if hospital_name:
            beds[hospital_name] = bed

    return beds


def get_realtime_bed_map() -> dict[str, RealtimeBed]:
    global _cached_at, _cached_beds

    now = time.time()
    if _cached_beds is not None and now - _cached_at < CACHE_TTL_SECONDS:
        return _cached_beds

    _cached_beds = _fetch_realtime_beds()
    _cached_at = now
    return _cached_beds
