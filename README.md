# 대학교 수강신청 시스템

> 무신사 AI NATIVE ENGINEER 채용 2차 과제로 제출했던 프로젝트 복사본입니다.
> 2차 과제 전형에 합격한 결과물이며, 과제 원문과 프롬프트 활용 등은 제외하고 구현 내용을 공개합니다.

수강신청/취소, 강좌 조회, 시간표 조회 등을 제공하는 REST API 서버입니다.

## 기술 스택

- **언어**: Python 3.11+
- **프레임워크**: FastAPI
- **DB**: SQLite (in-memory) — 외부 DB 설치 불필요
- **ORM**: SQLAlchemy 2.0

## 빠른 시작

### 1. 의존성 설치

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

서버가 시작되면 초기 데이터(12,000명 학생, 600개 강좌 등)가 자동 생성됩니다 (~0.5초).

### 3. 동작 확인

```bash
curl http://localhost:8000/health
# {"status":"ok","database":"connected","counts":{"students":12000,"courses":600,"professors":120}}
```

## API 서버 정보

| 항목 | 값 |
|------|-----|
| 포트 | 8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| API 문서 | [docs/API.md](docs/API.md) |

## 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /health | 헬스체크 |
| GET | /students | 학생 목록 조회 |
| GET | /professors | 교수 목록 조회 |
| GET | /courses | 강좌 목록 조회 (전체/학과별) |
| GET | /courses/{id} | 강좌 상세 조회 |
| POST | /enrollments | 수강신청 |
| DELETE | /enrollments/{id} | 수강취소 |
| GET | /students/{id}/timetable | 시간표 조회 |

## 테스트 실행

```bash
python -m pytest tests/ -v
```

### 테스트 포함 항목
- 헬스체크
- 학생/교수/강좌 목록 조회
- 수강신청/취소 비즈니스 로직
- **동시성 테스트**: 정원 1명 남은 강좌에 100명 동시 신청 → 1명만 성공 검증
- **학점 제한 동시성 테스트**: 동일 학생 7과목 동시 신청 → 18학점 이하 보장

## 프로젝트 구조

```
├── README.md              # 이 파일
├── CLAUDE.md              # AI 에이전트 지침
├── requirements.txt       # Python 의존성
├── docs/
│   ├── REQUIREMENTS.md    # 요구사항 분석 및 설계 결정
│   └── API.md             # API 명세
├── src/
│   ├── main.py            # FastAPI 앱 엔트리포인트
│   ├── config.py          # 설정값
│   ├── database.py        # SQLAlchemy 엔진/세션
│   ├── models.py          # DB 모델
│   ├── schemas.py         # Pydantic 스키마
│   ├── seed.py            # 초기 데이터 생성기
│   ├── routers/           # API 엔드포인트
│   └── services/          # 비즈니스 로직
└── tests/                 # 테스트
```

## 문서

- [요구사항 분석 및 설계 결정](docs/REQUIREMENTS.md)
- [API 명세](docs/API.md)
