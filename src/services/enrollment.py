"""
수강신청/취소 비즈니스 로직 + 동시성 제어

동시성 전략 (Defense in Depth):
1. Application Layer: threading.Lock으로 student/course 단위 직렬화
2. DB Layer: enrolled < capacity 원자적 검증
3. DB Constraint: UNIQUE(student_id, course_id) 중복 방어

Lock 획득 순서: student_lock → course_lock (데드락 방지)
"""

import threading
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from src.models import Student, Course, CourseSchedule, Enrollment
from src.config import MAX_CREDITS_PER_SEMESTER


class LockManager:
    """리소스별 세밀한 락 관리자"""

    def __init__(self):
        self._meta_lock = threading.Lock()
        self._student_locks: dict[int, threading.Lock] = {}
        self._course_locks: dict[int, threading.Lock] = {}

    def get_student_lock(self, student_id: int) -> threading.Lock:
        with self._meta_lock:
            if student_id not in self._student_locks:
                self._student_locks[student_id] = threading.Lock()
            return self._student_locks[student_id]

    def get_course_lock(self, course_id: int) -> threading.Lock:
        with self._meta_lock:
            if course_id not in self._course_locks:
                self._course_locks[course_id] = threading.Lock()
            return self._course_locks[course_id]


lock_manager = LockManager()


class EnrollmentError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def _get_current_credits(student_id: int, db: Session) -> int:
    """학생의 현재 수강신청 총 학점"""
    enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.course))
        .filter(Enrollment.student_id == student_id)
        .all()
    )
    return sum(e.course.credits for e in enrollments)


def _get_student_schedules(student_id: int, db: Session) -> list[CourseSchedule]:
    """학생의 현재 수강신청된 모든 강좌의 스케줄"""
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()
    if not enrollments:
        return []

    course_ids = [e.course_id for e in enrollments]
    return db.query(CourseSchedule).filter(CourseSchedule.course_id.in_(course_ids)).all()


def _has_time_conflict(
    existing_schedules: list[CourseSchedule],
    new_schedules: list[CourseSchedule],
) -> bool:
    """
    시간 충돌 검사.
    끝 시간 == 시작 시간은 충돌이 아님 (strict inequality).
    """
    for existing in existing_schedules:
        for new in new_schedules:
            if existing.day_of_week != new.day_of_week:
                continue
            # 충돌 조건: start_a < end_b AND start_b < end_a
            if existing.start_time < new.end_time and new.start_time < existing.end_time:
                return True
    return False


def enroll_student(student_id: int, course_id: int, db: Session) -> dict:
    """
    수강신청 처리.
    2-레벨 락으로 동시성 안전 보장: student_lock → course_lock
    ORM detach 이슈 방지를 위해 dict로 반환.
    """
    student_lock = lock_manager.get_student_lock(student_id)
    course_lock = lock_manager.get_course_lock(course_id)

    with student_lock:
        with course_lock:
            # Lock 획득 후 세션 캐시 초기화 → 다른 스레드의 커밋 결과를 확실히 반영
            db.expire_all()

            # 1. 학생 존재 확인
            student = db.get(Student, student_id)
            if not student:
                raise EnrollmentError(404, "학생을 찾을 수 없습니다")

            # 2. 강좌 존재 확인 (스케줄 포함 로드)
            course = (
                db.query(Course)
                .options(joinedload(Course.schedules))
                .filter(Course.id == course_id)
                .first()
            )
            if not course:
                raise EnrollmentError(404, "강좌를 찾을 수 없습니다")

            # 3. 정원 확인 (핵심 동시성 체크)
            if course.enrolled >= course.capacity:
                raise EnrollmentError(409, "수강 정원이 초과되었습니다")

            # 4. 중복 수강신청 확인
            existing = (
                db.query(Enrollment)
                .filter(
                    Enrollment.student_id == student_id,
                    Enrollment.course_id == course_id,
                )
                .first()
            )
            if existing:
                raise EnrollmentError(409, "이미 수강신청한 강좌입니다")

            # 5. 학점 제한 확인
            current_credits = _get_current_credits(student_id, db)
            if current_credits + course.credits > MAX_CREDITS_PER_SEMESTER:
                raise EnrollmentError(
                    409,
                    f"최대 학점({MAX_CREDITS_PER_SEMESTER})을 초과합니다. "
                    f"현재 {current_credits}학점, 신청 강좌 {course.credits}학점",
                )

            # 6. 시간 충돌 확인
            student_schedules = _get_student_schedules(student_id, db)
            if _has_time_conflict(student_schedules, course.schedules):
                raise EnrollmentError(409, "시간표가 겹치는 강좌가 있습니다")

            # 7. 수강신청 등록
            enrollment = Enrollment(student_id=student_id, course_id=course_id)
            db.add(enrollment)
            course.enrolled += 1

            # 커밋 전에 강좌 정보를 미리 추출 (ORM detach 방지)
            course_name = course.name
            course_code = course.course_code
            credits = course.credits

            db.commit()

            # 커밋 후 enrollment ID 조회
            created = (
                db.query(Enrollment.id, Enrollment.created_at)
                .filter(
                    Enrollment.student_id == student_id,
                    Enrollment.course_id == course_id,
                )
                .first()
            )

            return {
                "id": created[0] if created else 0,
                "student_id": student_id,
                "course_id": course_id,
                "course_name": course_name,
                "course_code": course_code,
                "credits": credits,
                "created_at": created[1] if created else datetime.now(timezone.utc),
            }


def cancel_enrollment(enrollment_id: int, student_id: int, db: Session) -> None:
    """
    수강취소 처리.
    student_lock → course_lock 순서로 획득.
    """
    # 먼저 enrollment을 조회해서 course_id 확인
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )

    if not enrollment:
        raise EnrollmentError(404, "수강신청 내역을 찾을 수 없습니다")

    if enrollment.student_id != student_id:
        raise EnrollmentError(403, "본인의 수강신청만 취소할 수 있습니다")

    target_course_id = enrollment.course_id

    student_lock = lock_manager.get_student_lock(student_id)
    course_lock = lock_manager.get_course_lock(target_course_id)

    with student_lock:
        with course_lock:
            # 삭제 전 다시 확인 (락 획득 사이에 이미 삭제됐을 수 있음)
            enrollment = db.get(Enrollment, enrollment_id)
            if not enrollment:
                raise EnrollmentError(404, "수강신청 내역을 찾을 수 없습니다")

            course = db.get(Course, enrollment.course_id)
            db.delete(enrollment)
            if course and course.enrolled > 0:
                course.enrolled -= 1
            db.commit()
