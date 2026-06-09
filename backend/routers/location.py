from fastapi import APIRouter, HTTPException, Query

from schemas.location import LocationSearchResponse
from services.location_service import search_location


router = APIRouter(prefix="/location", tags=["location"])


@router.get("/search", response_model=LocationSearchResponse)
def search_location_endpoint(q: str = Query(..., min_length=2, max_length=80)):
    results = search_location(q)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="검색 결과가 없습니다. 주소나 장소명을 조금 더 구체적으로 입력해 주세요.",
        )

    return {
        "query": q,
        "results": results,
    }
