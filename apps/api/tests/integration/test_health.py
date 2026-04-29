def test_health_returns_200(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}


def test_unknown_route_returns_structured_error_with_request_id(client):
    response = client.get("/api/v1/not-here", headers={"X-Request-ID": "req_test"})

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Resource not found.",
            "details": None,
            "request_id": "req_test",
        }
    }

