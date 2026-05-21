import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Professor, Department
from src.schemas import ProfessorResponse, ProfessorListResponse, PaginationMeta
from src.config import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/professors", tags=["Professors"])


@router.get("", response_model=ProfessorListResponse)
def list_professors(
    page: int = Query(DEFAULT_PAGE, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    department_id: int | None = Query(None, description="학과 ID로 필터링"),
    db: Session = Depends(get_db),
):
    query = db.query(Professor).join(Department)

    if department_id is not None:
        query = query.filter(Professor.department_id == department_id)

    total_count = query.count()
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    professors = query.order_by(Professor.id).offset((page - 1) * size).limit(size).all()

    return ProfessorListResponse(
        data=[
            ProfessorResponse(
                id=p.id,
                name=p.name,
                department_id=p.department_id,
                department_name=p.department.name,
            )
            for p in professors
        ],
        pagination=PaginationMeta(
            page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
        ),
    )
