from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models import Student, Enrollment, Course, CourseSchedule
from src.schemas import (
    EnrollmentRequest,
    EnrollmentResponse,
    TimetableResponse,
    TimetableEntry,
    ScheduleSlot,
)
from src.services.enrollment import enroll_student, cancel_enrollment, EnrollmentError
from src.config import MAX_CREDITS_PER_SEMESTER
from src.seed import DAYS

router = APIRouter(tags=["Enrollments"])


def _format_schedule_str(schedules) -> str:
    day_order = {d: i for i, d in enumerate(DAYS)}
    sorted_s = sorted(schedules, key=lambda s: (day_order.get(s.day_of_week, 99), s.start_time))
    return ", ".join(f"{s.day_of_week} {s.start_time}-{s.end_time}" for s in sorted_s)


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=201)
def create_enrollment(req: EnrollmentRequest, db: Session = Depends(get_db)):
    """수강신청"""
    try:
        result = enroll_student(req.student_id, req.course_id, db)
    except EnrollmentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return EnrollmentResponse(**result)


@router.delete("/enrollments/{enrollment_id}", status_code=204)
def delete_enrollment(
    enrollment_id: int,
    student_id: int = Query(..., description="수강취소 요청 학생 ID"),
    db: Session = Depends(get_db),
):
    """수강취소"""
    try:
        cancel_enrollment(enrollment_id, student_id, db)
    except EnrollmentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/students/{student_id}/timetable", response_model=TimetableResponse)
def get_timetable(student_id: int, db: Session = Depends(get_db)):
    """학생의 이번 학기 시간표 조회"""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")

    enrollments = (
        db.query(Enrollment)
        .options(
            joinedload(Enrollment.course).joinedload(Course.schedules),
            joinedload(Enrollment.course).joinedload(Course.professor),
        )
        .filter(Enrollment.student_id == student_id)
        .all()
    )

    total_credits = sum(e.course.credits for e in enrollments)

    entries = []
    for e in enrollments:
        c = e.course
        entries.append(
            TimetableEntry(
                enrollment_id=e.id,
                course_id=c.id,
                course_name=c.name,
                course_code=c.course_code,
                credits=c.credits,
                professor_name=c.professor.name,
                schedule=_format_schedule_str(c.schedules),
                schedules=[
                    ScheduleSlot(
                        day_of_week=s.day_of_week,
                        start_time=s.start_time,
                        end_time=s.end_time,
                    )
                    for s in c.schedules
                ],
            )
        )

    return TimetableResponse(
        student_id=student_id,
        student_name=student.name,
        total_credits=total_credits,
        max_credits=MAX_CREDITS_PER_SEMESTER,
        entries=entries,
    )
