def test_list_courses(client):
    resp = client.get("/courses?size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total_count"] >= 500
    assert len(data["data"]) == 5
    course = data["data"][0]
    assert "id" in course
    assert "name" in course
    assert "credits" in course
    assert "capacity" in course
    assert "enrolled" in course
    assert "schedule" in course


def test_list_courses_by_department(client):
    resp = client.get("/courses?department_id=1&size=5")
    assert resp.status_code == 200
    data = resp.json()
    for course in data["data"]:
        assert course["department_id"] == 1


def test_get_course(client):
    resp = client.get("/courses/1")
    assert resp.status_code == 200
    course = resp.json()
    assert course["id"] == 1


def test_get_course_not_found(client):
    resp = client.get("/courses/999999")
    assert resp.status_code == 404


def test_list_students(client):
    resp = client.get("/students?size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total_count"] >= 10000


def test_list_professors(client):
    resp = client.get("/professors?size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total_count"] >= 100
