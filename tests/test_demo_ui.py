from fastapi.testclient import TestClient

from main import app


def test_demo_ui_serves_html() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "rag-eval-lab demo UI" in response.text
