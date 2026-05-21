import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models import Course, CourseSchedule, Department
from src.schemas import (
    CourseResponse,
    CourseListResponse,
    ScheduleSlot,
    PaginationMeta,
)
from src.config import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.seed import DAYS

router = APIRouter(prefix="/courses", tags=["Courses"])


def _format_schedule_str(schedules: list) -> str:
    """CourseSchedule 목록 → "월 09:00-10:30, 수 09:00-10:30" """
    day_order = {d: i for i, d in enumerate(DAYS)}
    sorted_s = sorted(schedules, key=lambda s: (day_order.get(s.day_of_week, 99), s.start_time))
    return ", ".join(f"{s.day_of_week} {s.start_time}-{s.end_time}" for s in sorted_s)


def _course_to_response(course: Course) -> CourseResponse:
    return CourseResponse(
        id=course.id,
        name=course.name,
        course_code=course.course_code,
        credits=course.credits,
        capacity=course.capacity,
        enrolled=course.enrolled,
        professor_id=course.professor_id,
        professor_name=course.professor.name,
        department_id=course.department_id,
        department_name=course.department.name,
        schedule=_format_schedule_str(course.schedules),
        schedules=[
            ScheduleSlot(
                day_of_week=s.day_of_week,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in course.schedules
        ],
    )


@router.get("", response_model=CourseListResponse)
def list_courses(
    page: int = Query(DEFAULT_PAGE, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    department_id: int | None = Query(None, description="학과 ID로 필터링"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Course)
        .options(joinedload(Course.schedules), joinedload(Course.professor), joinedload(Course.department))
    )

    if department_id is not None:
        query = query.filter(Course.department_id == department_id)

    # joinedload produces duplicates with pagination, so use subquery for count
    count_query = db.query(Course)
    if department_id is not None:
        count_query = count_query.filter(Course.department_id == department_id)
    total_count = count_query.count()
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    courses = (
        query.order_by(Course.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    # deduplicate (joinedload can cause dups with offset/limit)
    seen = set()
    unique_courses = []
    for c in courses:
        if c.id not in seen:
            seen.add(c.id)
            unique_courses.append(c)

    return CourseListResponse(
        data=[_course_to_response(c) for c in unique_courses],
        pagination=PaginationMeta(
            page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
        ),
    )


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = (
        db.query(Course)
        .options(joinedload(Course.schedules), joinedload(Course.professor), joinedload(Course.department))
        .filter(Course.id == course_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="강좌를 찾을 수 없습니다")
    return _course_to_response(course)
