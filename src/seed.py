"""
초기 데이터 생성기
- 12개 학과, 120명 교수, 600개 강좌, 12,000명 학생
- 현실적인 한국 대학 데이터
- 교수 시간표 충돌 없이 강좌 스케줄 생성
"""

import random
from sqlalchemy.orm import Session

from src.models import Department, Professor, Course, CourseSchedule, Student


# ── 토큰 데이터 ─────────────────────────────────────────────

DEPARTMENT_NAMES = [
    "컴퓨터공학과",
    "전자공학과",
    "기계공학과",
    "화학공학과",
    "건축학과",
    "경영학과",
    "경제학과",
    "심리학과",
    "영어영문학과",
    "수학과",
    "물리학과",
    "생명과학과",
]

FAMILY_NAMES = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
    "홍", "고", "문", "양", "손", "배", "백", "허", "유", "남",
]

GIVEN_NAMES = [
    "민준", "서윤", "지호", "하은", "서준", "수빈", "도윤", "지아",
    "예준", "하윤", "시우", "서연", "주원", "민서", "하준", "지윤",
    "지후", "채원", "준서", "은서", "현우", "소율", "우진", "다은",
    "준혁", "예은", "건우", "수아", "선우", "지원", "민재", "소연",
    "유준", "예림", "승현", "채은", "태윤", "하린", "정우", "윤서",
    "지환", "나윤", "승우", "미래", "연우", "시은", "재윤", "유나",
    "은호", "세은", "동현", "가은", "시현", "서현", "재민", "다인",
    "성민", "윤아", "현준", "아린",
]

# 학과별 강좌명 토큰 (기본 과목명 -> 접두/접미사 조합으로 확장)
COURSE_BASES = {
    "컴퓨터공학과": [
        "프로그래밍", "자료구조", "알고리즘", "운영체제", "컴퓨터네트워크",
        "데이터베이스", "소프트웨어공학", "인공지능", "컴퓨터구조", "웹프로그래밍",
        "컴파일러", "정보보안", "분산시스템", "기계학습", "모바일프로그래밍",
    ],
    "전자공학과": [
        "회로이론", "전자기학", "디지털회로", "신호와시스템", "통신이론",
        "반도체공학", "제어공학", "전력전자", "마이크로프로세서", "임베디드시스템",
        "광공학", "RF공학", "센서공학", "전자회로설계", "디지털신호처리",
    ],
    "기계공학과": [
        "정역학", "동역학", "열역학", "유체역학", "재료역학",
        "기계설계", "기계제작", "자동제어", "로봇공학", "CAD/CAM",
        "열전달", "에너지공학", "진동학", "유한요소법", "기계시스템설계",
    ],
    "화학공학과": [
        "화학공학개론", "반응공학", "분리공정", "열전달", "물질전달",
        "공정설계", "고분자공학", "촉매공학", "생물화학공학", "나노재료",
        "환경공학", "공정제어", "전기화학", "식품공학", "에너지화학공학",
    ],
    "건축학과": [
        "건축설계", "건축구조학", "건축환경", "건축재료", "건축시공",
        "도시계획", "건축법규", "건축CAD", "실내건축", "건축역사",
        "구조역학", "건설관리", "친환경건축", "BIM설계", "건축음향학",
    ],
    "경영학과": [
        "경영학원론", "마케팅", "재무관리", "인적자원관리", "경영전략",
        "회계원리", "생산운영관리", "경영정보시스템", "국제경영", "조직행동론",
        "소비자행동", "경영통계", "브랜드관리", "투자론", "창업경영",
    ],
    "경제학과": [
        "경제학원론", "미시경제학", "거시경제학", "국제경제학", "계량경제학",
        "화폐금융론", "재정학", "산업조직론", "노동경제학", "경제사",
        "게임이론", "개발경제학", "환경경제학", "행동경제학", "금융경제학",
    ],
    "심리학과": [
        "심리학개론", "발달심리학", "인지심리학", "사회심리학", "이상심리학",
        "상담심리학", "심리통계", "실험심리학", "성격심리학", "산업심리학",
        "신경심리학", "건강심리학", "범죄심리학", "교육심리학", "심리검사",
    ],
    "영어영문학과": [
        "영어학개론", "영문학개론", "영작문", "영어회화", "영어음성학",
        "영어통사론", "영미소설", "영미시", "영어의미론", "번역연습",
        "영미문화", "영어교육론", "비즈니스영어", "미디어영어", "영어담화분석",
    ],
    "수학과": [
        "미적분학", "선형대수학", "해석학", "대수학", "확률론",
        "수리통계학", "미분방정식", "이산수학", "위상수학", "수치해석",
        "복소해석학", "정수론", "조합론", "편미분방정식", "금융수학",
    ],
    "물리학과": [
        "일반물리학", "역학", "전자기학", "양자역학", "열통계물리학",
        "광학", "현대물리학", "고체물리학", "핵물리학", "천체물리학",
        "전산물리학", "플라즈마물리학", "입자물리학", "물리수학", "반도체물리",
    ],
    "생명과학과": [
        "일반생물학", "세포생물학", "분자생물학", "유전학", "생화학",
        "미생물학", "생태학", "발생생물학", "면역학", "신경생물학",
        "식물생리학", "동물생리학", "진화생물학", "바이오인포매틱스", "생물통계학",
    ],
}

COURSE_SUFFIXES = ["", " 기초", " 심화", " 특론", " 실습", " 세미나"]

DAYS = ["월", "화", "수", "목", "금"]

TIME_SLOTS = [
    ("09:00", "10:30"),
    ("10:30", "12:00"),
    ("13:00", "14:30"),
    ("14:30", "16:00"),
    ("16:00", "17:30"),
]


def _format_schedule(schedules: list[dict]) -> str:
    """CourseSchedule dicts → 사람이 읽기 좋은 문자열"""
    parts = []
    for s in sorted(schedules, key=lambda x: (DAYS.index(x["day"]), x["start"])):
        parts.append(f"{s['day']} {s['start']}-{s['end']}")
    return ", ".join(parts)


def _generate_schedules_for_course(
    credits: int,
    professor_slots: set[tuple[str, str]],
    rng: random.Random,
) -> list[dict] | None:
    """
    교수의 기존 시간표와 충돌하지 않는 스케줄을 생성.
    실패하면 None 반환.
    """
    num_sessions = 2 if credits >= 3 else 1
    available = [
        (day, start, end)
        for day in DAYS
        for start, end in TIME_SLOTS
        if (day, start) not in professor_slots
    ]

    if len(available) < num_sessions:
        return None

    if num_sessions == 2:
        # 같은 시간대, 다른 요일 우선 시도 (현실적)
        slot = rng.choice(TIME_SLOTS)
        matching_days = [d for d in DAYS if (d, slot[0]) not in professor_slots]
        if len(matching_days) >= 2:
            chosen_days = rng.sample(matching_days, 2)
            return [
                {"day": d, "start": slot[0], "end": slot[1]}
                for d in chosen_days
            ]

    # 폴백: 랜덤 선택
    chosen = rng.sample(available, num_sessions)
    return [{"day": d, "start": s, "end": e} for d, s, e in chosen]


def generate_seed_data(db: Session) -> None:
    # 이미 데이터가 있으면 스킵 (idempotent)
    if db.query(Department).first() is not None:
        return

    rng = random.Random(42)  # 재현 가능한 시드

    # 1. 학과 생성
    departments = []
    for name in DEPARTMENT_NAMES:
        dept = Department(name=name)
        db.add(dept)
        departments.append(dept)
    db.flush()

    # 2. 교수 생성 (학과당 10명 = 120명)
    professors = []
    prof_idx = 0
    for dept in departments:
        for _ in range(10):
            family = rng.choice(FAMILY_NAMES)
            given = rng.choice(GIVEN_NAMES)
            prof = Professor(name=f"{family}{given}", department_id=dept.id)
            db.add(prof)
            professors.append(prof)
            prof_idx += 1
    db.flush()

    # 3. 강좌 생성 (교수당 5개 = 600개)
    # 교수별 사용 중인 시간 슬롯 추적
    professor_used_slots: dict[int, set[tuple[str, str]]] = {
        p.id: set() for p in professors
    }

    courses = []
    course_counter = 0
    for dept in departments:
        dept_professors = [p for p in professors if p.department_id == dept.id]
        base_names = COURSE_BASES.get(dept.name, COURSE_BASES["컴퓨터공학과"])

        for prof in dept_professors:
            for course_idx in range(5):
                base = base_names[course_idx % len(base_names)]
                suffix_idx = course_idx // len(base_names)
                suffix = COURSE_SUFFIXES[suffix_idx % len(COURSE_SUFFIXES)]
                course_name = f"{base}{suffix}"

                credits = rng.choices([2, 3, 3, 3, 4], k=1)[0]  # 3학점 비율 높게
                capacity = rng.choice([30, 40, 50, 60, 80, 100])

                dept_code = dept.name[:2]
                course_counter += 1
                course_code = f"{dept_code}{course_counter:04d}"

                schedules = _generate_schedules_for_course(
                    credits, professor_used_slots[prof.id], rng
                )
                if schedules is None:
                    # 시간대가 부족하면 슬롯 초기화하고 재시도
                    schedules = _generate_schedules_for_course(
                        credits, set(), rng
                    )
                    if schedules is None:
                        continue

                course = Course(
                    name=course_name,
                    course_code=course_code,
                    credits=credits,
                    capacity=capacity,
                    enrolled=0,
                    professor_id=prof.id,
                    department_id=dept.id,
                )
                db.add(course)
                db.flush()

                for s in schedules:
                    cs = CourseSchedule(
                        course_id=course.id,
                        day_of_week=s["day"],
                        start_time=s["start"],
                        end_time=s["end"],
                    )
                    db.add(cs)
                    professor_used_slots[prof.id].add((s["day"], s["start"]))

                courses.append(course)

    db.flush()

    # 4. 학생 생성 (학과당 1,000명 = 12,000명)
    student_number_counter = 20210001
    students_batch = []
    for dept in departments:
        for _ in range(1000):
            family = rng.choice(FAMILY_NAMES)
            given = rng.choice(GIVEN_NAMES)
            grade = rng.choice([1, 1, 2, 2, 3, 3, 4])  # 저학년 비중 높게

            student = Student(
                name=f"{family}{given}",
                student_number=str(student_number_counter),
                department_id=dept.id,
                grade=grade,
            )
            students_batch.append(student)
            student_number_counter += 1

    db.add_all(students_batch)
    db.commit()
