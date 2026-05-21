import pytest
from starlette.testclient import TestClient

from src.main import app


@pytest.fixture(scope="session")
def client():
    """세션 단위로 TestClient 공유 (lifespan으로 시드 데이터 1회 생성)"""
    with TestClient(app) as c:
        yield c
