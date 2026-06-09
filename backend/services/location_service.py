from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


class LocationSearchError(RuntimeError):
    pass


def _read_kakao_api_key() -> str:
    return (
        os.getenv("KAKAO_REST_API_KEY", "").strip()
        or os.getenv("KAKAO_MOBILITY_REST_API_KEY", "").strip()
    )


def _request_kakao_local(url: str, params: dict[str, str | int]) -> dict | None:
    api_key = _read_kakao_api_key()
    if not api_key:
        raise LocationSearchError("Kakao REST API key is not configured.")

    query_string = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{url}?{query_string}",
        headers={"Authorization": f"KakaoAK {api_key}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=3.0) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise LocationSearchError("Kakao Local API authorization failed.") from exc
        return None
    except (TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return None


def _result_key(result: dict) -> tuple[str, str]:
    return (str(result.get("lat", "")), str(result.get("lon", "")))


def search_location(query: str, limit: int = 5) -> list[dict]:
    query = str(query).strip()
    if not query:
        return []

    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    address_payload = _request_kakao_local(
        KAKAO_ADDRESS_SEARCH_URL,
        {"query": query, "size": limit},
    )
    for item in (address_payload or {}).get("documents", []):
        lon = item.get("x")
        lat = item.get("y")
        if lon is None or lat is None:
            continue

        road_address = item.get("road_address") or {}
        address = item.get("address") or {}
        result = {
            "name": str(road_address.get("building_name") or item.get("address_name") or query),
            "address": str(road_address.get("address_name") or address.get("address_name") or item.get("address_name") or ""),
            "lat": float(lat),
            "lon": float(lon),
            "source": "kakao_address",
        }
        key = _result_key(result)
        if key not in seen:
            results.append(result)
            seen.add(key)

    if len(results) < limit:
        keyword_payload = _request_kakao_local(
            KAKAO_KEYWORD_SEARCH_URL,
            {"query": query, "size": limit},
        )
        for item in (keyword_payload or {}).get("documents", []):
            lon = item.get("x")
            lat = item.get("y")
            if lon is None or lat is None:
                continue

            result = {
                "name": str(item.get("place_name") or item.get("address_name") or query),
                "address": str(item.get("road_address_name") or item.get("address_name") or ""),
                "lat": float(lat),
                "lon": float(lon),
                "source": "kakao_keyword",
            }
            key = _result_key(result)
            if key not in seen:
                results.append(result)
                seen.add(key)

            if len(results) >= limit:
                break

    return results[:limit]
