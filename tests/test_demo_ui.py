from fastapi.testclient import TestClient

from main import app


def test_demo_ui_serves_html() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "rag-eval-lab" in response.text
    assert "Run comparison" in response.text
    assert "/static/demo.css" in response.text
    assert "/static/demo.js" in response.text
    assert "embedding_strong_rerank" in response.text


def test_demo_ui_serves_static_assets() -> None:
    client = TestClient(app)

    css_response = client.get("/static/demo.css")
    js_response = client.get("/static/demo.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "javascript" in js_response.headers["content-type"]
    assert ".result-card" in css_response.text
    assert "selectedStrategies" in js_response.text
    assert "/qa/query" in js_response.text
