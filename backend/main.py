from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.health import router as health_router
from routers.location import router as location_router
from routers.triage import router as triage_router


app = FastAPI(
    title="Gangwon Emergency Hospital Guide API",
    description="강원도 맞춤형 응급 및 상시 병원 안내 시스템 백엔드 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://gangwon-emergency-hospital-guide.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(location_router, prefix="/api")
app.include_router(triage_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "Gangwon Emergency Hospital Guide API",
        "status": "running",
    }
