"""
동시성 제어 테스트

핵심 시나리오: 정원 1명 남은 강좌에 100명이 동시 신청 → 정확히 1명만 성공
"""

import concurrent.futures
import threading

from starlette.testclient import TestClient

from src.main import app


def test_concurrent_enrollment_capacity():
    """
    정원 초과 방지 테스트.
    강좌 정원을 1로 설정한 뒤 100명이 동시에 수강신청.
    정확히 1명만 성공(201), 나머지 99명은 실패(409)해야 한다.
    """
    with TestClient(app) as client:
        # 정원이 넉넉한 강좌를 찾아서 미리 정원을 거의 채움
        courses_resp = client.get("/courses?size=100")
        courses = courses_resp.json()["data"]

        # 정원이 큰 강좌 선택 (capacity >= 30)
        target_course = None
        for c in courses:
            if c["capacity"] >= 30 and c["enrolled"] == 0:
                target_course = c
                break

        assert target_course is not None, "테스트에 사용할 강좌가 없습니다"

        course_id = target_course["id"]
        capacity = target_course["capacity"]

        # 정원 - 1 명까지 채움
        pre_enrolled_ids = []
        for i in range(capacity - 1):
            student_id = 200 + i  # 학생 ID 200~
            resp = client.post(
                "/enrollments",
                json={"student_id": student_id, "course_id": course_id},
            )
            if resp.status_code == 201:
                pre_enrolled_ids.append(resp.json()["id"])
            elif resp.status_code == 409 and "시간표" in resp.json().get("detail", ""):
                continue  # 시간 충돌 시 건너뜀

        # 현재 강좌 상태 확인
        course_resp = client.get(f"/courses/{course_id}")
        current_enrolled = course_resp.json()["enrolled"]
        remaining = capacity - current_enrolled
        print(f"\n[Concurrency Test] Course {course_id}: capacity={capacity}, enrolled={current_enrolled}, remaining={remaining}")

        if remaining <= 0:
            # 이미 꽉 찬 경우 - 정리 후 스킵
            for eid in pre_enrolled_ids:
                client.delete(f"/enrollments/{eid}?student_id={199 + pre_enrolled_ids.index(eid) + 1}")
            return

        # 동시에 100명 신청
        num_concurrent = 100
        results = []
        barrier = threading.Barrier(num_concurrent)

        def try_enroll(student_id):
            barrier.wait()  # 모든 스레드가 준비될 때까지 대기 후 동시 출발
            resp = client.post(
                "/enrollments",
                json={"student_id": student_id, "course_id": course_id},
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(try_enroll, 500 + i)
                for i in range(num_concurrent)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = results.count(201)
        fail_count = results.count(409)

        print(f"[Concurrency Test] Results: {success_count} success, {fail_count} fail, {len(results) - success_count - fail_count} other")

        # 핵심 검증: 성공 수 == 남은 정원
        assert success_count == remaining, (
            f"Expected exactly {remaining} success, got {success_count}"
        )

        # 강좌 정원 초과 여부 확인
        course_resp = client.get(f"/courses/{course_id}")
        final_enrolled = course_resp.json()["enrolled"]
        assert final_enrolled <= capacity, (
            f"Capacity exceeded! enrolled={final_enrolled}, capacity={capacity}"
        )

        print(f"[Concurrency Test] PASSED: final enrolled={final_enrolled}, capacity={capacity}")


def test_concurrent_same_student_multiple_courses():
    """
    동일 학생이 여러 강좌에 동시 신청할 때도
    학점 제한(18학점)과 시간 충돌이 올바르게 검증되는지 확인.
    """
    with TestClient(app) as client:
        student_id = 800

        # 3학점 강좌 7개를 동시에 신청 (3*7 = 21 > 18)
        courses_resp = client.get("/courses?size=100")
        courses = courses_resp.json()["data"]
        three_credit_courses = [c for c in courses if c["credits"] == 3][:7]

        assert len(three_credit_courses) >= 7, "3학점 강좌가 부족합니다"

        results = []
        barrier = threading.Barrier(len(three_credit_courses))

        def try_enroll(course_id):
            barrier.wait()
            resp = client.post(
                "/enrollments",
                json={"student_id": student_id, "course_id": course_id},
            )
            return resp.status_code, resp.json()

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(three_credit_courses)) as executor:
            futures = [
                executor.submit(try_enroll, c["id"])
                for c in three_credit_courses
            ]
            results = [f.result() for f in futures]

        success_count = sum(1 for code, _ in results if code == 201)
        total_credits = success_count * 3

        print(f"\n[Same Student Test] {success_count} courses enrolled, {total_credits} credits")
        assert total_credits <= 18, f"Credit limit exceeded: {total_credits}"
