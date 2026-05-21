from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Student, Course, Professor

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """서버 상태 및 DB 연결, 데이터 건수 확인"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok",
        "database": db_status,
        "counts": {
            "students": db.query(Student).count(),
            "courses": db.query(Course).count(),
            "professors": db.query(Professor).count(),
        },
    }
