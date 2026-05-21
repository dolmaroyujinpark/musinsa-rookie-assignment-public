# CLAUDE.md - AI 에이전트 지침

## 프로젝트 개요
대학교 수강신청 REST API 서버. Python + FastAPI + SQLite(in-memory).

## 핵심 원칙
1. **동시성 안전**: 정원 초과 절대 불가. threading.Lock으로 course/student 단위 락 적용.
2. **빌드 즉시 실행**: 외부 DB 불필요. `pip install` → `uvicorn` 으로 즉시 기동.
3. **REST 원칙 준수**: 명확한 HTTP 메서드/상태코드 사용.

## 기술 스택
- Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite in-memory
- 테스트: pytest + httpx (FastAPI TestClient)

## 프로젝트 구조
```
src/
├── main.py          # FastAPI 앱, lifespan (시드 데이터 생성)
├── config.py        # 설정값
├── database.py      # SQLAlchemy 엔진/세션
├── models.py        # DB 모델 (Department, Professor, Course, Student, Enrollment 등)
├── schemas.py       # Pydantic 요청/응답 스키마
├── seed.py          # 초기 데이터 생성기
├── routers/         # API 엔드포인트
│   ├── health.py
│   ├── students.py
│   ├── courses.py
│   ├── professors.py
│   └── enrollments.py
└── services/
    └── enrollment.py # 수강신청/취소 비즈니스 로직 + 동시성 제어
```

## 동시성 제어 전략
- **2-레벨 락**: student_lock → course_lock 순서로 획득 (데드락 방지)
- **DB 제약**: UNIQUE(student_id, course_id)로 중복 방어
- **낙관적 검증**: enrolled < capacity 체크 후 enrolled += 1

## 비즈니스 규칙
- 최대 18학점
- 시간 충돌 불가 (끝 시간 == 시작 시간은 허용)
- 동일 강좌 중복 수강신청 불가
- 인증 없음 (student_id 직접 전달)

## 코딩 컨벤션
- snake_case (Python 표준)
- API 응답 필드: snake_case
- 에러 응답: `{"detail": "에러 메시지"}`
- 목록 조회: 페이지네이션 적용 (page/size 파라미터)

## 테스트 실행
```bash
cd project-root
python -m pytest tests/ -v
```

## 서버 실행
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```
