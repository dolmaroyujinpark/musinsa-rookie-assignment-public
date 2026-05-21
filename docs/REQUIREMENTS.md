# 요구사항 분석 및 설계 결정

## 1. 요구사항 분류

### 1.1 명시적 요구사항

기획팀 메모와 과제 문서에서 직접 도출한 요구사항:

| # | 요구사항 | 출처 |
|---|---------|------|
| R1 | 학생 목록 조회 | 기획팀 메모 |
| R2 | 강좌 목록 조회 (전체/학과별, 정원·현재인원·시간 포함) | 기획팀 메모 |
| R3 | 교수 목록 조회 | 기획팀 메모 |
| R4 | 수강신청 | 기획팀 메모 |
| R5 | 수강취소 | 기획팀 메모 |
| R6 | 내 시간표(이번 학기) 조회 | 기획팀 메모 |
| R7 | 학생당 최대 18학점 제한 | 기획팀 메모 |
| R8 | 같은 시간대 중복 수강 불가 | 기획팀 메모 |
| R9 | 정원 초과 절대 불가 (100명 동시 → 1명만 성공) | 기획팀 메모 |
| R10 | GET /health → 200 OK | 과제 문서 |
| R11 | REST API 형식 | 과제 문서 |
| R12 | 동적 데이터 생성 (1분 이내) | 과제 문서 |
| R13 | 최소 데이터: 학과 10, 강좌 500, 학생 10,000, 교수 100 | 과제 문서 |

### 1.2 암묵적 요구사항 (도출 + 결정)

기획팀 메모에 명시되지 않았으나, 시스템 구현에 필수적인 결정 사항:

#### A. 인증/인가

**결정**: 인증 없이, 요청 body에 `student_id`를 직접 포함

**근거**:
- 기획팀이 인증에 대해 언급하지 않음
- 과제의 핵심은 동시성 제어이므로, 인증에 시간을 투자하면 본질에서 벗어남
- 평가자가 curl로 즉시 테스트 가능해야 하므로 인증 없는 것이 편리
- 프로덕션에서는 JWT 기반 인증을 추가하되, 현재 단계에서는 MVP 범위 외로 판단

**트레이드오프**: 보안 없음. 다른 학생의 ID로 수강신청/취소가 가능. 프로덕션 전 반드시 인증 추가 필요.

#### B. 시간 충돌 판정 기준

**결정**: 끝 시간 == 시작 시간은 충돌이 아님 (semi-open interval: `[start, end)`)

**근거**:
- 실제 대학에서 10:30에 A강좌가 끝나고 10:30에 B강좌가 시작하는 것은 일반적
- 충돌 조건: `start_A < end_B AND start_B < end_A` (strict inequality)

**대안**: 끝 시간 == 시작 시간도 충돌로 판정 → 쉬는 시간 보장, 하지만 수강 선택지 제한

#### C. 시간표 슬롯 정의

**결정**:
- 요일: 월~금 (5일)
- 시간대: 09:00~17:30, 1.5시간 단위 (5슬롯/일)
  - 09:00-10:30, 10:30-12:00, 13:00-14:30, 14:30-16:00, 16:00-17:30
- 점심시간: 12:00~13:00 (강의 없음)

**근거**: 한국 대학의 일반적인 운영 방식을 참고

#### D. 학점 분포

**결정**:
- 학점 범위: 2~4학점
- 분포: 3학점 비율이 가장 높음 (약 60%)
- 2학점: 실습/세미나, 4학점: 심화 과목

**근거**: 한국 대학의 일반적인 학점 체계. 1학점 과목은 드물어 제외.

#### E. 강좌 스케줄

**결정**:
- 2학점 과목: 주 1회 (1.5시간)
- 3학점 과목: 주 2회 (각 1.5시간)
- 4학점 과목: 주 2회 (각 1.5시간)

**근거**: 교수 시간표 충돌 없이 현실적인 스케줄 생성을 위해 단순화

#### F. 동일 강좌 중복 수강신청

**결정**: 불가 (UNIQUE 제약으로 강제)

**근거**: 수강신청 시스템의 기본 상식. 이미 신청한 강좌를 다시 신청할 이유 없음.

#### G. 수강취소 제한

**결정**: 제한 없음 (자유롭게 취소 가능)

**근거**: MVP 단계에서는 단순화. 프로덕션에서는 수강취소 기간 정책 추가 필요.

#### H. 선수과목/학년 제한

**결정**: 미구현 (향후 확장 사항으로 문서화)

**근거**: 핵심 기능(수강신청/취소/동시성)에 집중. 데이터 모델에 `grade` 필드는 포함하여 확장 가능.

#### I. 페이지네이션

**결정**: offset 기반 페이지네이션 (page/size 파라미터)

**근거**: 학생 10,000명을 한 번에 반환하면 성능 문제. 기본 20건, 최대 100건.

---

## 2. 동시성 제어 전략

### 2.1 문제 정의

> "정원이 1명 남은 강좌에 100명이 동시에 신청해도, 정확히 1명만 성공해야 합니다."

이 요구사항은 **정원 초과 방지**를 절대적으로 보장해야 함을 의미합니다.

### 2.2 전략: Defense in Depth (다층 방어)

#### Layer 1: Application Lock (threading.Lock)

```
student_lock → course_lock 순서로 획득 (데드락 방지)
```

- **LockManager**: 리소스 ID별로 개별 Lock을 관리
- **student_lock**: 동일 학생의 동시 요청을 직렬화 → 학점 초과/시간 충돌 방지
- **course_lock**: 동일 강좌에 대한 동시 요청을 직렬화 → 정원 초과 방지
- **Lock 획득 순서 고정**: 항상 student → course 순서로 획득하여 데드락 원천 차단

#### Layer 2: DB Constraint

- `UNIQUE(student_id, course_id)`: 중복 수강신청을 DB 레벨에서 방어
- 애플리케이션 로직을 우회하더라도 데이터 무결성 보장

#### Layer 3: 비즈니스 로직 검증

Lock 획득 후, 트랜잭션 내에서 다음을 순차 검증:
1. 학생 존재 확인
2. 강좌 존재 확인
3. 정원 확인 (`enrolled < capacity`)
4. 중복 수강신청 확인
5. 학점 제한 확인 (현재 학점 + 신청 학점 ≤ 18)
6. 시간 충돌 확인

### 2.3 검토한 대안들과 선택 근거

동시성 제어 전략을 결정하기 위해 세 가지 접근법을 비교 검토했습니다.

#### 대안 1: 글로벌 Lock (기각)

```python
global_lock = threading.Lock()
with global_lock:
    # 모든 수강신청을 직렬 처리
```

- **장점**: 구현 단순, 정확성 보장 용이
- **단점**: 모든 수강신청이 직렬화됨. 학생 A가 강좌 X를 신청하는 동안 학생 B가 강좌 Y를 신청할 수 없음 → 수강신청 기간 대량 트래픽에 병목
- **기각 이유**: 기획팀이 "서버가 다운되어 불만 폭주"를 문제로 지적했으므로, 성능을 완전히 무시하는 설계는 부적절

#### 대안 2: DB 레벨 Lock — SELECT FOR UPDATE (현재 환경에서 불가)

```sql
SELECT * FROM courses WHERE id = ? FOR UPDATE;
-- row-level lock 획득
UPDATE courses SET enrolled = enrolled + 1 WHERE id = ? AND enrolled < capacity;
```

- **장점**: DB가 정합성을 보장하므로 애플리케이션 레벨 Lock 불필요
- **단점**: SQLite는 row-level lock 미지원 (database-level lock만 가능). PostgreSQL 필요.
- **기각 이유**: 평가자 환경에 PostgreSQL 설치를 전제할 수 없음

#### 대안 3: 낙관적 락 — 버전 카운터 (부분 채택)

```sql
UPDATE courses SET enrolled = enrolled + 1, version = version + 1
WHERE id = ? AND enrolled < capacity AND version = ?;
-- affected_rows == 0이면 재시도
```

- **장점**: Lock 없이 동시성 제어 가능, 성능 좋음
- **단점**: 정원 충돌만 해결. 학점 초과/시간 충돌은 별도 메커니즘 필요. 재시도 로직 복잡.
- **부분 채택**: `enrolled < capacity` 검증은 현재 전략에 포함. 단, 완전한 낙관적 락 대신 비관적 Lock과 결합.

#### 최종 선택: 리소스별 비관적 Lock (채택)

- **정확성 보장**: Lock 내에서 모든 비즈니스 규칙을 원자적으로 검증
- **적절한 병렬성**: 다른 학생/강좌 조합은 병렬 처리 가능
- **데드락 방지**: Lock 획득 순서 고정 (student → course)
- **세션 캐시 갱신**: Lock 진입 시 `db.expire_all()`로 다른 스레드의 커밋 결과를 반드시 반영

### 2.4 enrolled 비정규화의 정합성 관리

`Course.enrolled`는 `enrollments` 테이블의 COUNT와 동기화되어야 하는 비정규화 필드입니다.

**정합성 보장 방법**:
- 수강신청 시: Lock 내에서 `enrolled += 1`과 INSERT를 동일 트랜잭션에서 수행
- 수강취소 시: Lock 내에서 `enrolled -= 1`과 DELETE를 동일 트랜잭션에서 수행
- 두 연산 모두 course_lock 보호 하에 실행되므로, enrolled와 실제 COUNT의 불일치 가능성 없음

**만약 불일치가 발생한다면**: 주기적으로 `UPDATE courses SET enrolled = (SELECT COUNT(*) FROM enrollments WHERE course_id = courses.id)` 배치 보정 실행 가능. 현재 구조에서는 Lock이 정합성을 보장하므로 불필요.

**매번 COUNT(*) 대신 비정규화를 선택한 이유**: 강좌 목록 조회 시 모든 강좌의 현재 인원을 표시해야 하는데, 600개 강좌 × JOIN COUNT는 쿼리 비용이 높음. enrolled 컬럼으로 단일 SELECT로 해결.

### 2.5 SQLite 선택 이유

- **외부 의존 없음**: 평가자가 추가 설치 없이 즉시 실행 가능
- **StaticPool**: 모든 요청이 같은 in-memory DB를 공유
- **단점**: row-level lock 미지원 → 애플리케이션 레벨 Lock으로 보완
- **프로덕션 전환 시**: PostgreSQL + `SELECT ... FOR UPDATE` + `SERIALIZABLE` 격리 수준 권장

### 2.6 단일 프로세스 한계와 스케일링 전략

현재 구현은 **단일 프로세스(single process)**에서 `threading.Lock`으로 동시성을 제어합니다.

**한계**: uvicorn 워커를 여러 개 띄우거나 서버를 수평 확장하면, 프로세스 간 Lock이 공유되지 않아 동시성 제어가 깨집니다.

**스케일링 시 전환 전략**:

| 단계 | 방법 | 비용 |
|------|------|------|
| 수직 확장 | 단일 프로세스, 스레드 풀 확대 | 낮음 (현재 구조 유지) |
| DB 전환 | PostgreSQL + `SELECT FOR UPDATE` | 중간 (Lock 로직을 DB 트랜잭션으로 이관) |
| 분산 Lock | Redis SETNX 기반 분산 Lock | 높음 (Redis 인프라 필요) |

현재 단계에서는 단일 프로세스로 충분하며, 실제 수강신청 트래픽(수만 명 동시)이 발생하면 PostgreSQL + 분산 Lock으로 전환합니다.

### 2.7 구현 중 발견한 엣지 케이스

#### StaticPool 세션 캐시 이슈

**문제**: StaticPool(단일 연결)에서 Thread A가 수강신청을 커밋한 후, Thread B의 SQLAlchemy 세션이 이전 상태를 캐시하고 있어 학점 합계가 갱신되지 않는 현상.

**원인**: SQLAlchemy 세션은 identity map에 ORM 객체를 캐시합니다. Thread A의 커밋이 DB에 반영되어도, Thread B의 세션에는 캐시된 이전 상태가 남아있을 수 있습니다.

**해결**: Lock 획득 직후 `db.expire_all()`을 호출하여 세션의 모든 캐시 객체를 만료시킵니다. 이후 쿼리는 DB에서 최신 데이터를 다시 읽습니다.

```python
with student_lock:
    with course_lock:
        db.expire_all()  # 캐시 무효화 → 최신 데이터 보장
        # 이후 모든 쿼리는 fresh read
```

이 패턴은 **StaticPool + threading 조합**에서 필수적이며, 일반적인 connection pool에서는 각 요청이 독립된 연결을 사용하므로 불필요합니다.

---

## 3. 데이터 모델

### 3.1 ERD

```
Department (1) ──── (*) Professor
Department (1) ──── (*) Course
Department (1) ──── (*) Student
Professor  (1) ──── (*) Course
Course     (1) ──── (*) CourseSchedule
Course     (1) ──── (*) Enrollment
Student    (1) ──── (*) Enrollment
```

### 3.2 테이블 설계

| 테이블 | 주요 필드 | 비고 |
|--------|----------|------|
| departments | id, name(UNIQUE) | 12개 학과 |
| professors | id, name, department_id(FK) | 120명 |
| courses | id, name, course_code(UNIQUE), credits, capacity, enrolled, professor_id(FK), department_id(FK) | 600개. enrolled는 비정규화 카운터 |
| course_schedules | id, course_id(FK), day_of_week, start_time, end_time | 강좌별 1~2개 시간 슬롯 |
| students | id, name, student_number(UNIQUE), department_id(FK), grade | 12,000명 |
| enrollments | id, student_id(FK), course_id(FK), created_at | UNIQUE(student_id, course_id) |

---

## 4. 시드 데이터 생성 전략

- **결정론적 시드** (`random.Random(42)`): 매 실행마다 동일한 데이터 보장
- **교수 시간표 충돌 방지**: 강좌 생성 시 교수의 기존 스케줄을 추적하여 겹치지 않게 배정
- **현실적 이름 생성**: 한국 성(30개) + 이름(60개) 토큰 조합
- **학과별 강좌명**: 학과별 15개 기본 과목명 + 접미사(기초, 심화, 특론, 실습, 세미나) 조합
- **생성 시간**: 약 0.5초 (1분 제한 대비 충분한 여유)

---

## 5. API 설계 원칙

- **RESTful**: 리소스 중심 URL, 적절한 HTTP 메서드와 상태 코드
- **일관된 응답 형식**: 목록은 `{data: [], pagination: {}}`, 단건은 객체 직접 반환
- **에러 응답**: `{"detail": "에러 메시지"}` 형식, 적절한 HTTP 상태 코드
- **페이지네이션**: `page`와 `size` 쿼리 파라미터

---

## 6. 프론트엔드 연동 고려사항

기획팀이 "프론트팀에서 따로 작업할 예정"이라고 명시했으므로, 프론트 연동에 필요한 사항을 사전 반영했습니다.

- **CORS 미들웨어**: `CORSMiddleware`로 브라우저에서의 cross-origin 요청 허용. 프로덕션에서는 `allow_origins`를 특정 도메인으로 제한.
- **일관된 에러 응답**: 모든 에러가 `{"detail": "..."}` JSON 형식으로 반환되므로, 프론트에서 일관된 에러 처리 가능.
- **Swagger UI**: `/docs` 경로에서 자동 생성된 API 문서를 확인할 수 있어, 프론트 팀이 별도 문서 없이도 API를 탐색 가능.
- **페이지네이션 메타데이터**: `total_count`, `total_pages`를 포함하여 프론트에서 페이지 네비게이션 구현 가능.

---

## 7. 향후 확장 고려사항

구현하지 않았으나 설계 시 고려한 사항을 우선순위 순으로 정리합니다.

### 높은 우선순위 (프로덕션 필수)

1. **인증/인가**: JWT 기반 토큰 인증. 학생 본인만 수강신청/취소 가능. 현재 `student_id`를 body에 직접 전달하는 방식은 보안 취약점이므로, 프로덕션 전 반드시 전환 필요.
2. **수강신청 기간 관리**: 수강신청 시작/종료 시각 설정, 기간 외 요청 차단. `settings` 테이블에 기간 정보를 저장하고 미들웨어에서 체크.
3. **PostgreSQL 마이그레이션**: 프로덕션 트래픽을 감당하려면 SQLite에서 PostgreSQL로 전환 필요. Alembic으로 마이그레이션 관리. `SELECT FOR UPDATE` + `SERIALIZABLE` 격리 수준 활용.

### 중간 우선순위 (사용자 경험 향상)

4. **선수과목 체계**: `course_prerequisites` 중간 테이블로 선수과목 관계 표현. 수강신청 시 이수 여부 검증.
5. **학년별 수강 제한**: Student.grade와 Course에 min_grade 필드 추가. 1학년이 4학년 전공심화를 수강하는 것을 방지.
6. **대기열(Waitlist)**: 정원 초과 시 대기열 등록 → 취소 발생 시 대기 순서대로 자동 배정.
7. **감사 로그**: 수강신청/취소 이력을 별도 테이블에 기록. 분쟁 발생 시 추적 근거.

### 낮은 우선순위 (운영 고도화)

8. **실시간 알림**: WebSocket으로 잔여 정원 실시간 업데이트. 수강신청 기간 중 학생들이 정원 현황을 실시간으로 확인.
9. **Rate Limiting**: 동일 학생의 과도한 요청(매크로 등) 차단. Token bucket 알고리즘 적용.
10. **모니터링**: Prometheus 메트릭 수집 + Grafana 대시보드. 수강신청 TPS, 에러율, 응답 시간 모니터링.
