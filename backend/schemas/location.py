from pydantic import BaseModel


class LocationSearchResult(BaseModel):
    name: str
    address: str
    lat: float
    lon: float
    source: str


class LocationSearchResponse(BaseModel):
    query: str
    results: list[LocationSearchResult]
