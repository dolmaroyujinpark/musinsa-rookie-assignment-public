# API 명세

Base URL: `http://localhost:8000`

CORS가 활성화되어 있으므로 브라우저에서 직접 호출 가능합니다.

모든 에러 응답은 `{"detail": "에러 메시지"}` 형식입니다.

---

## Health Check

### `GET /health`

서버 정상 구동 및 DB 연결 상태, 시드 데이터 건수를 확인합니다.

**Response**: `200 OK`

```json
{
  "status": "ok",
  "database": "connected",
  "counts": {
    "students": 12000,
    "courses": 600,
    "professors": 120
  }
}
```

---

## 학생 (Students)

### `GET /students`

학생 목록을 페이지네이션하여 조회합니다.

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | int | N | 1 | 페이지 번호 (≥1) |
| size | int | N | 20 | 페이지 크기 (1~100) |
| department_id | int | N | - | 학과 ID로 필터링 |

**Response**: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "name": "송민서",
      "student_number": "20210001",
      "department_id": 1,
      "department_name": "컴퓨터공학과",
      "grade": 2
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 12000,
    "total_pages": 600
  }
}
```

---

## 교수 (Professors)

### `GET /professors`

교수 목록을 페이지네이션하여 조회합니다.

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | int | N | 1 | 페이지 번호 |
| size | int | N | 20 | 페이지 크기 (1~100) |
| department_id | int | N | - | 학과 ID로 필터링 |

**Response**: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "name": "홍지아",
      "department_id": 1,
      "department_name": "컴퓨터공학과"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 120,
    "total_pages": 6
  }
}
```

---

## 강좌 (Courses)

### `GET /courses`

강좌 목록을 페이지네이션하여 조회합니다.

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | int | N | 1 | 페이지 번호 |
| size | int | N | 20 | 페이지 크기 (1~100) |
| department_id | int | N | - | 학과 ID로 필터링 |

**Response**: `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "name": "프로그래밍",
      "course_code": "컴퓨0001",
      "credits": 2,
      "capacity": 50,
      "enrolled": 0,
      "professor_id": 1,
      "professor_name": "홍지아",
      "department_id": 1,
      "department_name": "컴퓨터공학과",
      "schedule": "화 16:00-17:30",
      "schedules": [
        {
          "day_of_week": "화",
          "start_time": "16:00",
          "end_time": "17:30"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total_count": 600,
    "total_pages": 30
  }
}
```

### `GET /courses/{course_id}`

강좌 상세 조회.

**Path Parameters**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| course_id | int | 강좌 ID |

**Response**: `200 OK`

```json
{
  "id": 2,
  "name": "자료구조",
  "course_code": "컴퓨0002",
  "credits": 3,
  "capacity": 40,
  "enrolled": 0,
  "professor_id": 1,
  "professor_name": "홍지아",
  "department_id": 1,
  "department_name": "컴퓨터공학과",
  "schedule": "월 16:00-17:30, 금 16:00-17:30",
  "schedules": [
    {"day_of_week": "월", "start_time": "16:00", "end_time": "17:30"},
    {"day_of_week": "금", "start_time": "16:00", "end_time": "17:30"}
  ]
}
```

**Error Responses**:

| 상태 코드 | 조건 | 응답 |
|----------|------|------|
| 404 | 존재하지 않는 강좌 | `{"detail": "강좌를 찾을 수 없습니다"}` |

---

## 수강신청 (Enrollments)

### `POST /enrollments`

수강신청을 등록합니다.

**Request Body**:

```json
{
  "student_id": 1,
  "course_id": 2
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| student_id | int | Y | 학생 ID |
| course_id | int | Y | 강좌 ID |

**Response**: `201 Created`

```json
{
  "id": 1,
  "student_id": 1,
  "course_id": 2,
  "course_name": "자료구조",
  "course_code": "컴퓨0002",
  "credits": 3,
  "created_at": "2026-02-08T15:30:00"
}
```

**Error Responses**:

| 상태 코드 | 조건 | 응답 |
|----------|------|------|
| 404 | 학생을 찾을 수 없음 | `{"detail": "학생을 찾을 수 없습니다"}` |
| 404 | 강좌를 찾을 수 없음 | `{"detail": "강좌를 찾을 수 없습니다"}` |
| 409 | 정원 초과 | `{"detail": "수강 정원이 초과되었습니다"}` |
| 409 | 중복 수강신청 | `{"detail": "이미 수강신청한 강좌입니다"}` |
| 409 | 학점 제한 초과 | `{"detail": "최대 학점(18)을 초과합니다. 현재 15학점, 신청 강좌 4학점"}` |
| 409 | 시간 충돌 | `{"detail": "시간표가 겹치는 강좌가 있습니다"}` |
| 422 | 잘못된 요청 형식 | Pydantic 유효성 검증 에러 |

### `DELETE /enrollments/{enrollment_id}`

수강취소를 처리합니다.

**Path Parameters**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| enrollment_id | int | 수강신청 ID |

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| student_id | int | Y | 수강취소 요청 학생 ID |

**Response**: `204 No Content`

(응답 본문 없음)

**Error Responses**:

| 상태 코드 | 조건 | 응답 |
|----------|------|------|
| 404 | 수강신청 내역 없음 | `{"detail": "수강신청 내역을 찾을 수 없습니다"}` |
| 403 | 본인의 수강신청이 아님 | `{"detail": "본인의 수강신청만 취소할 수 있습니다"}` |

**예시**:

```bash
curl -X DELETE "http://localhost:8000/enrollments/1?student_id=1"
```

---

## 시간표 (Timetable)

### `GET /students/{student_id}/timetable`

학생의 이번 학기 시간표를 조회합니다.

**Path Parameters**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| student_id | int | 학생 ID |

**Response**: `200 OK`

```json
{
  "student_id": 1,
  "student_name": "송민서",
  "total_credits": 6,
  "max_credits": 18,
  "entries": [
    {
      "enrollment_id": 1,
      "course_id": 2,
      "course_name": "자료구조",
      "course_code": "컴퓨0002",
      "credits": 3,
      "professor_name": "홍지아",
      "schedule": "월 16:00-17:30, 금 16:00-17:30",
      "schedules": [
        {"day_of_week": "월", "start_time": "16:00", "end_time": "17:30"},
        {"day_of_week": "금", "start_time": "16:00", "end_time": "17:30"}
      ]
    }
  ]
}
```

**Error Responses**:

| 상태 코드 | 조건 | 응답 |
|----------|------|------|
| 404 | 학생을 찾을 수 없음 | `{"detail": "학생을 찾을 수 없습니다"}` |

---

## 공통 사항

### 에러 응답 형식

모든 에러는 아래 형식을 따릅니다:

```json
{
  "detail": "에러 메시지 (한글)"
}
```

### HTTP 상태 코드 요약

| 코드 | 의미 | 사용 |
|------|------|------|
| 200 | OK | 조회 성공 |
| 201 | Created | 수강신청 성공 |
| 204 | No Content | 수강취소 성공 |
| 404 | Not Found | 리소스 없음 |
| 403 | Forbidden | 권한 없음 |
| 409 | Conflict | 비즈니스 규칙 위반 (정원 초과, 중복, 학점 초과, 시간 충돌) |
| 422 | Unprocessable Entity | 요청 형식 오류 |

### 자동 생성 API 문서

서버 실행 후 아래 URL에서 Swagger UI를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
