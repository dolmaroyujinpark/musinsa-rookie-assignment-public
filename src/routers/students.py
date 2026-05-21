import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Student, Department
from src.schemas import StudentResponse, StudentListResponse, PaginationMeta
from src.config import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=StudentListResponse)
def list_students(
    page: int = Query(DEFAULT_PAGE, ge=1, description="페이지 번호"),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="페이지 크기"),
    department_id: int | None = Query(None, description="학과 ID로 필터링"),
    db: Session = Depends(get_db),
):
    query = db.query(Student).join(Department)

    if department_id is not None:
        query = query.filter(Student.department_id == department_id)

    total_count = query.count()
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    students = query.order_by(Student.id).offset((page - 1) * size).limit(size).all()

    return StudentListResponse(
        data=[
            StudentResponse(
                id=s.id,
                name=s.name,
                student_number=s.student_number,
                department_id=s.department_id,
                department_name=s.department.name,
                grade=s.grade,
            )
            for s in students
        ],
        pagination=PaginationMeta(
            page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
        ),
    )
