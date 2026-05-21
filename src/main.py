import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.database import engine, Base, SessionLocal
from src.seed import generate_seed_data
from src.routers import health, students, courses, professors, enrollments

logger = logging.getLogger("uvicorn.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어: method, path, status, 소요시간을 기록"""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 테이블 생성 + 시드 데이터
    start = time.time()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        generate_seed_data(db)
    finally:
        db.close()
    elapsed = time.time() - start
    print(f"[Startup] 초기 데이터 생성 완료 ({elapsed:.2f}s)")
    yield
    # Shutdown
    print("[Shutdown] 서버 종료")


app = FastAPI(
    title="대학교 수강신청 시스템",
    description="수강신청/취소, 강좌 조회, 시간표 조회 등을 제공하는 REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# 프론트팀 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(professors.router)
app.include_router(enrollments.router)
