"""수강신청 비즈니스 로직 테스트"""


def _enroll(client, student_id, course_id):
    return client.post(
        "/enrollments",
        json={"student_id": student_id, "course_id": course_id},
    )


def _cancel(client, enrollment_id, student_id):
    return client.delete(f"/enrollments/{enrollment_id}?student_id={student_id}")


def _timetable(client, student_id):
    return client.get(f"/students/{student_id}/timetable")


def _find_available_course(client, size=100):
    """빈 자리가 있는 강좌를 찾아 반환"""
    resp = client.get(f"/courses?size={size}")
    for c in resp.json()["data"]:
        if c["enrolled"] < c["capacity"]:
            return c
    return None


class TestEnrollment:
    def test_enroll_success(self, client):
        course = _find_available_course(client)
        assert course is not None, "사용 가능한 강좌 없음"

        # 다른 테스트와 충돌하지 않는 학생 ID 사용 (10000번대)
        resp = _enroll(client, student_id=10001, course_id=course["id"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["student_id"] == 10001
        assert data["course_id"] == course["id"]
        # 정리
        _cancel(client, data["id"], student_id=10001)

    def test_duplicate_enrollment(self, client):
        course = _find_available_course(client)
        assert course is not None

        resp1 = _enroll(client, student_id=10002, course_id=course["id"])
        assert resp1.status_code == 201

        resp2 = _enroll(client, student_id=10002, course_id=course["id"])
        assert resp2.status_code == 409

        # 정리
        _cancel(client, resp1.json()["id"], student_id=10002)

    def test_cancel_enrollment(self, client):
        course = _find_available_course(client)
        assert course is not None

        resp = _enroll(client, student_id=10003, course_id=course["id"])
        assert resp.status_code == 201
        enrollment_id = resp.json()["id"]

        cancel_resp = _cancel(client, enrollment_id, student_id=10003)
        assert cancel_resp.status_code == 204

    def test_cancel_other_student(self, client):
        course = _find_available_course(client)
        assert course is not None

        resp = _enroll(client, student_id=10004, course_id=course["id"])
        assert resp.status_code == 201
        enrollment_id = resp.json()["id"]

        # 다른 학생이 취소 시도
        cancel_resp = _cancel(client, enrollment_id, student_id=10005)
        assert cancel_resp.status_code == 403

        # 정리
        _cancel(client, enrollment_id, student_id=10004)

    def test_timetable(self, client):
        course = _find_available_course(client)
        assert course is not None

        resp = _enroll(client, student_id=10006, course_id=course["id"])
        assert resp.status_code == 201

        tt = _timetable(client, student_id=10006)
        assert tt.status_code == 200
        data = tt.json()
        assert data["student_id"] == 10006
        assert data["total_credits"] > 0
        assert len(data["entries"]) == 1

        # 정리
        _cancel(client, resp.json()["id"], student_id=10006)

    def test_student_not_found(self, client):
        resp = _enroll(client, student_id=999999, course_id=1)
        assert resp.status_code == 404

    def test_course_not_found(self, client):
        resp = _enroll(client, student_id=1, course_id=999999)
        assert resp.status_code == 404

    def test_schedule_conflict(self, client):
        """같은 시간대 두 강좌 수강신청 시 두 번째가 거부되는지 검증"""
        student_id = 10200

        # 강좌 목록에서 시간이 겹치는 두 강좌를 찾는다
        courses_resp = client.get("/courses?size=100")
        courses = courses_resp.json()["data"]
        available = [c for c in courses if c["enrolled"] < c["capacity"] and c["schedules"]]

        # 첫 번째 강좌의 스케줄과 겹치는 두 번째 강좌를 탐색
        first_course = None
        conflict_course = None
        for c1 in available:
            for slot1 in c1["schedules"]:
                for c2 in available:
                    if c2["id"] == c1["id"]:
                        continue
                    for slot2 in c2["schedules"]:
                        if (
                            slot1["day_of_week"] == slot2["day_of_week"]
                            and slot1["start_time"] < slot2["end_time"]
                            and slot2["start_time"] < slot1["end_time"]
                        ):
                            first_course = c1
                            conflict_course = c2
                            break
                    if conflict_course:
                        break
                if conflict_course:
                    break
            if conflict_course:
                break

        assert first_course is not None, "시간 충돌 테스트용 강좌 쌍을 찾을 수 없음"

        # 첫 번째 강좌 등록 성공
        resp1 = _enroll(client, student_id=student_id, course_id=first_course["id"])
        assert resp1.status_code == 201, f"첫 번째 수강신청 실패: {resp1.text}"

        # 시간 겹치는 두 번째 강좌 등록 시도 → 409 기대
        resp2 = _enroll(client, student_id=student_id, course_id=conflict_course["id"])
        assert resp2.status_code == 409, (
            f"시간 충돌 강좌가 등록됨: {resp2.text}. "
            f"강좌1: {first_course['schedule']}, 강좌2: {conflict_course['schedule']}"
        )
        assert "시간표" in resp2.json()["detail"]

        # 정리
        _cancel(client, resp1.json()["id"], student_id=student_id)

    def test_credit_limit(self, client):
        """18학점 초과 시 수강신청 실패"""
        courses_resp = client.get("/courses?size=100")
        courses = courses_resp.json()["data"]
        four_credit_courses = [c for c in courses if c["credits"] == 4 and c["enrolled"] < c["capacity"]]

        student_id = 10100
        enrolled_ids = []
        total = 0
        for c in four_credit_courses:
            if total + c["credits"] > 18:
                # 이 시점에서 초과해야 함
                resp = _enroll(client, student_id=student_id, course_id=c["id"])
                assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
                break
            resp = _enroll(client, student_id=student_id, course_id=c["id"])
            if resp.status_code == 201:
                enrolled_ids.append(resp.json()["id"])
                total += c["credits"]
            elif resp.status_code == 409 and "시간표" in resp.json().get("detail", ""):
                continue  # 시간 충돌이면 건너뜀

        # 정리
        for eid in enrolled_ids:
            _cancel(client, eid, student_id=student_id)
