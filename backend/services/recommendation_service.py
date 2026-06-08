from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pandas as pd

from schemas.triage import RecommendedHospital
from services.data_loader import load_beds, load_eta_model, load_hospitals


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


def _match_department_score(hospital_department: str, target_department: str) -> int:
    hospital_department = str(hospital_department or "")
    target_department = str(target_department or "")

    if not target_department:
        return 0

    if target_department in hospital_department or hospital_department in target_department:
        return 35

    broad_map = {
        "심장내과": ["내과", "응급의학과"],
        "호흡기내과": ["내과", "응급의학과"],
        "소화기내과": ["내과", "응급의학과"],
        "신경과": ["신경외과", "내과", "응급의학과"],
        "정형외과": ["외과", "신경외과", "응급의학과"],
        "외과": ["정형외과", "응급의학과"],
        "소아청소년과": ["내과", "응급의학과"],
    }

    for alt in broad_map.get(target_department, []):
        if alt in hospital_department:
            return 20

    return 0


def recommend_hospitals(
    department: str,
    severity_level: int,
    user_lat: float | None = None,
    user_lon: float | None = None,
    limit: int = 3,
) -> list[RecommendedHospital]:
    hospitals = load_hospitals().copy()
    beds = load_beds()

    user_lat = user_lat or DEFAULT_USER_LAT
    user_lon = user_lon or DEFAULT_USER_LON

    hospitals = hospitals.dropna(subset=["lat", "lon"]).copy()

    # 응급도 1~2단계는 응급실 보유 병원을 우선 대상으로 한다.
    if severity_level <= 2 and "is_emergency" in hospitals.columns:
        emergency_candidates = hospitals[hospitals["is_emergency"] == 1].copy()
        if len(emergency_candidates) >= 3:
            hospitals = emergency_candidates

    hospitals["distance_km"] = hospitals.apply(
        lambda row: haversine_km(user_lat, user_lon, float(row["lat"]), float(row["lon"])),
        axis=1,
    )

    hospitals["eta_min"] = hospitals["distance_km"].apply(_predict_eta)

    hospitals["department_score"] = hospitals["department"].apply(
        lambda value: _match_department_score(value, department)
    )

    hospitals["emergency_score"] = hospitals["is_emergency"].apply(lambda value: 30 if int(value) == 1 else 0)
    hospitals["distance_score"] = hospitals["distance_km"].apply(lambda value: max(0, 25 - value * 0.8))
    hospitals["eta_score"] = hospitals["eta_min"].apply(lambda value: max(0, 25 - value * 0.5))
    hospitals["night_score"] = hospitals.get("night_service", 0).fillna(0).apply(lambda value: 5 if int(value) == 1 else 0)

    hospitals["recommendation_score"] = (
        hospitals["department_score"]
        + hospitals["emergency_score"]
        + hospitals["distance_score"]
        + hospitals["eta_score"]
        + hospitals["night_score"]
    ).round().astype(int)

    hospitals = hospitals.sort_values(
        ["recommendation_score", "is_emergency", "department_score"],
        ascending=[False, False, False],
    ).head(limit)

    bed_map = {}
    if not beds.empty:
        bed_map = dict(zip(beds["hospital_name"], beds["hvec"]))

    recommendations: list[RecommendedHospital] = []
    for rank, (_, row) in enumerate(hospitals.iterrows(), start=1):
        available_beds = int(bed_map.get(row["hospital_name"], 0))
        reason_parts = []

        if int(row.get("is_emergency", 0)) == 1:
            reason_parts.append("응급실 보유")
        if int(row.get("department_score", 0)) >= 20:
            reason_parts.append(f"{department} 관련 진료과 매칭")
        reason_parts.append(f"예상 이동시간 {int(row['eta_min'])}분")

        recommendations.append(
            RecommendedHospital(
                rank=rank,
                hospital_name=str(row["hospital_name"]),
                eta_min=int(row["eta_min"]),
                available_beds=available_beds,
                recommendation_score=int(row["recommendation_score"]),
                reason=" · ".join(reason_parts),
                department=str(row.get("department", "")),
                address=str(row.get("address", "")),
                phone=str(row.get("phone", "")),
                distance_km=round(float(row["distance_km"]), 2),
                is_emergency=int(row.get("is_emergency", 0)),
            )
        )

    return recommendations
