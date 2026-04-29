import uuid


def test_protected_endpoints_require_auth(client):
    response = client.get("/api/v1/chats")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_all_resource_paths_exist(authenticated_client):
    resource_id = uuid.uuid4()

    checks = [
        authenticated_client.post("/api/v1/upload-sessions", files={"file": ("sales.csv", "a,b\n1,2\n", "text/csv")}),
        authenticated_client.get(f"/api/v1/upload-sessions/{resource_id}"),
        authenticated_client.patch(f"/api/v1/upload-sessions/{resource_id}", json={"selected_sheet_name": "Orders"}),
        authenticated_client.delete(f"/api/v1/upload-sessions/{resource_id}"),
        authenticated_client.post("/api/v1/datasets", json={"upload_session_id": str(resource_id), "name": "Sales"}),
        authenticated_client.get("/api/v1/datasets"),
        authenticated_client.get(f"/api/v1/datasets/{resource_id}"),
        authenticated_client.get(f"/api/v1/datasets/{resource_id}/columns"),
        authenticated_client.get(f"/api/v1/datasets/{resource_id}/quality-issues"),
        authenticated_client.get(f"/api/v1/datasets/{resource_id}/preview"),
        authenticated_client.delete(f"/api/v1/datasets/{resource_id}"),
        authenticated_client.get("/api/v1/chats"),
        authenticated_client.post("/api/v1/chats", json={"dataset_id": str(resource_id)}),
        authenticated_client.get(f"/api/v1/chats/{resource_id}"),
        authenticated_client.patch(f"/api/v1/chats/{resource_id}", json={"title": "Revenue by Month"}),
        authenticated_client.delete(f"/api/v1/chats/{resource_id}"),
        authenticated_client.get(f"/api/v1/chats/{resource_id}/messages"),
        authenticated_client.post(
            f"/api/v1/chats/{resource_id}/messages",
            json={"content": "Show revenue by month"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        ),
        authenticated_client.get(f"/api/v1/analysis-runs/{resource_id}"),
    ]

    assert all(response.status_code != 405 for response in checks)
    assert all(response.status_code != 404 or response.json()["error"]["message"].endswith("not found.") for response in checks)


def test_standard_error_envelope_for_invalid_resource(authenticated_client):
    response = authenticated_client.post("/api/v1/chats", json={"dataset_id": str(uuid.uuid4())})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["request_id"].startswith("req_")


def test_unknown_resource_returns_404(authenticated_client):
    response = authenticated_client.get(f"/api/v1/chats/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_cross_tenant_placeholder_returns_not_found(authenticated_client):
    response = authenticated_client.get(f"/api/v1/datasets/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
