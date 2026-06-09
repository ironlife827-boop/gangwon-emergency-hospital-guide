from fastapi import APIRouter, HTTPException, Query

from schemas.location import LocationSearchResponse
from services.location_service import LocationSearchError, search_location


router = APIRouter(prefix="/location", tags=["location"])


@router.get("/search", response_model=LocationSearchResponse)
def search_location_endpoint(q: str = Query(..., min_length=2, max_length=80)):
    try:
        results = search_location(q)
    except LocationSearchError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "위치 검색 API 설정을 확인해 주세요. "
                "Render 환경변수 KAKAO_REST_API_KEY 또는 KAKAO_MOBILITY_REST_API_KEY가 필요합니다."
            ),
        ) from exc

    if not results:
        raise HTTPException(
            status_code=404,
            detail="검색 결과가 없습니다. 주소나 장소명을 조금 더 구체적으로 입력해 주세요.",
        )

    return {
        "query": q,
        "results": results,
    }
