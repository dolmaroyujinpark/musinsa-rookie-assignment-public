from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from src.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    professors = relationship("Professor", back_populates="department")
    courses = relationship("Course", back_populates="department")
    students = relationship("Student", back_populates="department")


class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    department = relationship("Department", back_populates="professors")
    courses = relationship("Course", back_populates="professor")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    course_code = Column(String, nullable=False, unique=True)
    credits = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    enrolled = Column(Integer, nullable=False, default=0)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    professor = relationship("Professor", back_populates="courses")
    department = relationship("Department", back_populates="courses")
    schedules = relationship("CourseSchedule", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_courses_department_id", "department_id"),
    )


class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day_of_week = Column(String(3), nullable=False)  # "월","화","수","목","금"
    start_time = Column(String(5), nullable=False)    # "09:00"
    end_time = Column(String(5), nullable=False)      # "10:30"

    course = relationship("Course", back_populates="schedules")

    __table_args__ = (
        Index("ix_course_schedules_course_id", "course_id"),
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    student_number = Column(String, nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    grade = Column(Integer, nullable=False)  # 1~4

    department = relationship("Department", back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_students_department_id", "department_id"),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
        Index("ix_enrollments_student_id", "student_id"),
        Index("ix_enrollments_course_id", "course_id"),
    )
