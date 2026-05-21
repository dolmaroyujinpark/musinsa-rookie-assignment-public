from datetime import datetime

from pydantic import BaseModel, Field


# ── Pagination ──────────────────────────────────────────────

class PaginationMeta(BaseModel):
    page: int
    size: int
    total_count: int
    total_pages: int


# ── Department ──────────────────────────────────────────────

class DepartmentResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ── Professor ──────────────────────────────────────────────

class ProfessorResponse(BaseModel):
    id: int
    name: str
    department_id: int
    department_name: str

    model_config = {"from_attributes": True}


# ── Course ─────────────────────────────────────────────────

class ScheduleSlot(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str

    model_config = {"from_attributes": True}


class CourseResponse(BaseModel):
    id: int
    name: str
    course_code: str
    credits: int
    capacity: int
    enrolled: int
    professor_id: int
    professor_name: str
    department_id: int
    department_name: str
    schedule: str  # 사람이 읽기 좋은 형태: "월 09:00-10:30, 수 09:00-10:30"
    schedules: list[ScheduleSlot]  # 프로그래밍 처리용

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    data: list[CourseResponse]
    pagination: PaginationMeta


# ── Student ────────────────────────────────────────────────

class StudentResponse(BaseModel):
    id: int
    name: str
    student_number: str
    department_id: int
    department_name: str
    grade: int

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    data: list[StudentResponse]
    pagination: PaginationMeta


# ── Professor List ─────────────────────────────────────────

class ProfessorListResponse(BaseModel):
    data: list[ProfessorResponse]
    pagination: PaginationMeta


# ── Enrollment ─────────────────────────────────────────────

class EnrollmentRequest(BaseModel):
    student_id: int = Field(..., description="수강신청할 학생 ID")
    course_id: int = Field(..., description="수강신청할 강좌 ID")


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    course_name: str
    course_code: str
    credits: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Timetable ──────────────────────────────────────────────

class TimetableEntry(BaseModel):
    enrollment_id: int
    course_id: int
    course_name: str
    course_code: str
    credits: int
    professor_name: str
    schedule: str
    schedules: list[ScheduleSlot]

    model_config = {"from_attributes": True}


class TimetableResponse(BaseModel):
    student_id: int
    student_name: str
    total_credits: int
    max_credits: int
    entries: list[TimetableEntry]


# ── Error ──────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
