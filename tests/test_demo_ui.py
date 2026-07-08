from fastapi.testclient import TestClient

from main import app


def test_demo_ui_serves_html() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "rag-eval-lab" in response.text
    assert "Run comparison" in response.text
    assert "embedding_strong_rerank" in response.text
    assert "selectedStrategies" in response.text
    assert "/qa/query" in response.text
