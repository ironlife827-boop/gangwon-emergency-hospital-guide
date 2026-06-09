from __future__ import annotations

import math
import urllib.parse
from datetime import datetime

import numpy as np
import pandas as pd

from schemas.triage import RecommendedHospital
from services.data_loader import load_beds, load_eta_model, load_hospitals
from services.eta_service import get_kakao_driving_eta
from services.realtime_bed_service import get_realtime_bed_map


DEFAULT_USER_LAT = 37.8813153  # 춘천시청 인근 기본 좌표
DEFAULT_USER_LON = 127.7299707


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _predict_eta(distance_km: float) -> int:
    model = load_eta_model()

    now = datetime.now()
    features = pd.DataFrame(
        [
            {
                "distance_km": distance_km,
                "hour": now.hour,
                "weekday": now.weekday(),
                "weather_type": "sunny",
                "rainfall": 0,
                "snowfall": 0,
                "avg_speed": 60,
                "mountain_area": 0,
                "tourist_season": 0,
            }
        ]
    )

    if model is not None:
        try:
            eta = float(model.predict(features)[0])
            return max(1, int(round(eta)))
        except Exception:
            pass

    # 모델 예측 실패 시 평균 45km/h 기준으로 대체
    return max(1, int(round(distance_km / 45 * 60)))


def _department_tokens(department_text: str) -> set[str]:
    return {
        token.strip()
        for token in str(department_text or "").split(",")
        if token.strip()
    }


def _match_department_score(hospital_department: str, target_department: str) -> int:
    hospital_department = str(hospital_department or "")
    target_department = str(target_department or "")
    hospital_tokens = _department_tokens(hospital_department)

    if not target_department:
        return 0

    if target_department in hospital_tokens:
        return 35

    broad_map = {
        "심장내과": ["내과", "응급의학과"],
        "호흡기내과": ["내과", "응급의학과"],
        "소화기내과": ["내과", "응급의학과"],
        "이비인후과": ["내과", "가정의학과", "소아청소년과"],
        "신경과": ["신경외과", "내과", "응급의학과"],
        "정형외과": ["외과", "신경외과", "응급의학과"],
        "외과": ["정형외과", "응급의학과"],
        "소아청소년과": ["내과", "응급의학과"],
    }

    for alt in broad_map.get(target_department, []):
        if alt in hospital_tokens:
            return 20

    return 0


def _kakao_route_url(
    origin_lat: float,
    origin_lon: float,
    hospital_name: str,
    destination_lat: float,
    destination_lon: float,
) -> str:
    origin = urllib.parse.quote(f"내 위치,{origin_lat},{origin_lon}", safe=",")
    destination = urllib.parse.quote(
        f"{hospital_name},{destination_lat},{destination_lon}",
        safe=",",
    )
    return f"https://map.kakao.com/link/by/car/{origin}/{destination}"


def _kakao_route_app_url(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
) -> str:
    return (
        "kakaomap://route"
        f"?sp={origin_lat},{origin_lon}"
        f"&ep={destination_lat},{destination_lon}"
        "&by=car"
    )


def _bed_score(available_beds: int, severity_level: int) -> int:
    if severity_level >= 3:
        return 0
    if available_beds >= 5:
        return 45
    if available_beds > 0:
        return 35
    if severity_level <= 2:
        return -120
    return -70


def _bed_status_for_row(row, realtime_bed_map: dict, static_bed_map: dict) -> pd.Series:
    realtime_bed = realtime_bed_map.get(str(row.get("hospital_id", ""))) or realtime_bed_map.get(
        str(row["hospital_name"])
    )
    if realtime_bed is not None:
        return pd.Series(
            {
                "available_beds": int(realtime_bed.emergency_beds),
                "bed_source": realtime_bed.source,
                "bed_updated_at": realtime_bed.updated_at,
            }
        )

    return pd.Series(
        {
            "available_beds": int(static_bed_map.get(row["hospital_name"], 0)),
            "bed_source": "static_csv",
            "bed_updated_at": None,
        }
    )


def recommend_hospitals(
    department: str,
    severity_level: int,
    user_lat: float | None = None,
    user_lon: float | None = None,
    limit: int = 3,
) -> list[RecommendedHospital]:
    hospitals = load_hospitals().copy()
    beds = load_beds()
    realtime_bed_map = get_realtime_bed_map()
    static_bed_map = {}
    if not beds.empty:
        static_bed_map = dict(zip(beds["hospital_name"], beds["hvec"]))

    location_was_provided = user_lat is not None and user_lon is not None
    user_lat = user_lat if user_lat is not None else DEFAULT_USER_LAT
    user_lon = user_lon if user_lon is not None else DEFAULT_USER_LON

    hospitals = hospitals.dropna(subset=["lat", "lon"]).copy()
    emergency_priority = severity_level <= 2

    # 응급도 1~2단계는 응급실 보유 병원을 우선 대상으로 한다.
    if emergency_priority and "is_emergency" in hospitals.columns:
        emergency_candidates = hospitals[hospitals["is_emergency"] == 1].copy()
        if len(emergency_candidates) >= 3:
            hospitals = emergency_candidates

    hospitals["distance_km"] = hospitals.apply(
        lambda row: haversine_km(user_lat, user_lon, float(row["lat"]), float(row["lon"])),
        axis=1,
    )

    hospitals["eta_min"] = hospitals["distance_km"].apply(_predict_eta)
    hospitals["eta_source"] = "estimated"

    hospitals["department_score"] = hospitals["department"].apply(
        lambda value: _match_department_score(value, department)
    )

    hospitals[["available_beds", "bed_source", "bed_updated_at"]] = hospitals.apply(
        lambda row: _bed_status_for_row(row, realtime_bed_map, static_bed_map),
        axis=1,
    )
    hospitals["bed_score"] = hospitals["available_beds"].apply(
        lambda value: _bed_score(int(value), severity_level)
    )
    hospitals["has_available_bed"] = hospitals["available_beds"].apply(lambda value: int(value) > 0)

    hospitals["emergency_score"] = hospitals["is_emergency"].apply(
        lambda value: 30 if emergency_priority and int(value) == 1 else 0
    )
    hospitals["primary_care_score"] = hospitals["is_emergency"].apply(
        lambda value: 30 if not emergency_priority and int(value) == 0 else (-20 if not emergency_priority else 0)
    )
    hospitals["distance_score"] = hospitals["distance_km"].apply(lambda value: max(0, 25 - value * 0.8))
    hospitals["eta_score"] = hospitals["eta_min"].apply(lambda value: max(0, 25 - value * 0.5))
    hospitals["night_score"] = hospitals.get("night_service", 0).fillna(0).apply(lambda value: 5 if int(value) == 1 else 0)

    hospitals["recommendation_score"] = (
        hospitals["department_score"]
        + hospitals["bed_score"]
        + hospitals["emergency_score"]
        + hospitals["primary_care_score"]
        + hospitals["distance_score"]
        + hospitals["eta_score"]
        + hospitals["night_score"]
    ).round().astype(int)

    if emergency_priority:
        hospitals = hospitals.sort_values(
            ["has_available_bed", "recommendation_score", "is_emergency", "department_score"],
            ascending=[False, False, False, False],
        ).head(max(limit, limit * 3))
    else:
        hospitals = hospitals.sort_values(
            ["recommendation_score", "department_score", "is_emergency", "eta_min"],
            ascending=[False, False, True, True],
        ).head(max(limit, limit * 5))

    if location_was_provided:
        for index, row in hospitals.iterrows():
            route_eta = get_kakao_driving_eta(
                origin_lat=float(user_lat),
                origin_lon=float(user_lon),
                destination_lat=float(row["lat"]),
                destination_lon=float(row["lon"]),
            )
            if route_eta is None:
                continue

            hospitals.at[index, "eta_min"] = route_eta.eta_min
            hospitals.at[index, "distance_km"] = route_eta.distance_km
            hospitals.at[index, "eta_source"] = route_eta.source

        hospitals["distance_score"] = hospitals["distance_km"].apply(lambda value: max(0, 25 - value * 0.8))
        hospitals["eta_score"] = hospitals["eta_min"].apply(lambda value: max(0, 25 - value * 0.5))
        hospitals["recommendation_score"] = (
            hospitals["department_score"]
            + hospitals["bed_score"]
            + hospitals["emergency_score"]
            + hospitals["primary_care_score"]
            + hospitals["distance_score"]
            + hospitals["eta_score"]
            + hospitals["night_score"]
        ).round().astype(int)

    if emergency_priority:
        hospitals = hospitals.sort_values(
            ["has_available_bed", "recommendation_score", "is_emergency", "department_score", "eta_min"],
            ascending=[False, False, False, False, True],
        ).head(limit)
    else:
        hospitals = hospitals.sort_values(
            ["recommendation_score", "department_score", "is_emergency", "eta_min"],
            ascending=[False, False, True, True],
        ).head(limit)

    recommendations: list[RecommendedHospital] = []
    for rank, (_, row) in enumerate(hospitals.iterrows(), start=1):
        available_beds = int(row.get("available_beds", 0))
        bed_source = str(row.get("bed_source", "static_csv"))
        bed_updated_at = row.get("bed_updated_at")

        reason_parts = []

        if emergency_priority and int(row.get("is_emergency", 0)) == 1:
            reason_parts.append("응급실 보유")
        if int(row.get("department_score", 0)) >= 20:
            reason_parts.append(f"{department} 관련 진료과 매칭")
        if emergency_priority:
            if available_beds > 0:
                reason_parts.append(f"가용 병상 {available_beds}개")
            else:
                reason_parts.append("가용 병상 0개")
        reason_parts.append(f"예상 이동시간 {int(row['eta_min'])}분")

        recommendations.append(
            RecommendedHospital(
                rank=rank,
                hospital_name=str(row["hospital_name"]),
                eta_min=int(row["eta_min"]),
                eta_source=str(row.get("eta_source", "estimated")),
                available_beds=available_beds,
                bed_source=bed_source,
                bed_updated_at=bed_updated_at,
                recommendation_score=int(row["recommendation_score"]),
                reason=" · ".join(reason_parts),
                department=str(row.get("department", "")),
                address=str(row.get("address", "")),
                phone=str(row.get("phone", "")),
                distance_km=round(float(row["distance_km"]), 2),
                lat=round(float(row["lat"]), 7),
                lon=round(float(row["lon"]), 7),
                route_url=_kakao_route_url(
                    origin_lat=float(user_lat),
                    origin_lon=float(user_lon),
                    hospital_name=str(row["hospital_name"]),
                    destination_lat=float(row["lat"]),
                    destination_lon=float(row["lon"]),
                ),
                route_app_url=_kakao_route_app_url(
                    origin_lat=float(user_lat),
                    origin_lon=float(user_lon),
                    destination_lat=float(row["lat"]),
                    destination_lon=float(row["lon"]),
                ),
                is_emergency=int(row.get("is_emergency", 0)),
            )
        )

    return recommendations
