from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


KAKAO_DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"


@dataclass(frozen=True)
class RouteEta:
    eta_min: int
    distance_km: float
    source: str


def _read_kakao_api_key() -> str:
    return os.getenv("KAKAO_MOBILITY_REST_API_KEY", "").strip()


def get_kakao_driving_eta(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    timeout_seconds: float = 2.5,
) -> RouteEta | None:
    api_key = _read_kakao_api_key()
    if not api_key:
        return None

    params = urllib.parse.urlencode(
        {
            "origin": f"{origin_lon},{origin_lat}",
            "destination": f"{destination_lon},{destination_lat}",
            "priority": "RECOMMEND",
            "car_fuel": "GASOLINE",
            "car_hipass": "false",
            "alternatives": "false",
            "summary": "true",
        }
    )
    request = urllib.request.Request(
        f"{KAKAO_DIRECTIONS_URL}?{params}",
        headers={"Authorization": f"KakaoAK {api_key}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None

    routes = payload.get("routes") or []
    if not routes:
        return None

    summary = routes[0].get("summary") or {}
    duration_seconds = summary.get("duration")
    distance_meters = summary.get("distance")

    if duration_seconds is None or distance_meters is None:
        return None

    try:
        eta_min = max(1, int(round(float(duration_seconds) / 60)))
        distance_km = round(float(distance_meters) / 1000, 2)
    except (TypeError, ValueError):
        return None

    return RouteEta(eta_min=eta_min, distance_km=distance_km, source="kakao_directions")
