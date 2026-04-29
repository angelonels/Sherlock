from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import delete

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.models import AppUser, UploadSession
from app.main import app
from app.services.upload_safety import temp_file_path


@pytest.fixture
def db_user() -> AppUser:
    async def create_user() -> AppUser:
        user = AppUser(
            clerk_user_id=f"user_upload_{uuid.uuid4().hex}",
            email="upload@example.com",
            first_name="Upload",
            last_name="Tester",
        )
        async with SessionLocal() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    import asyncio

    return asyncio.run(create_user())


@pytest.fixture
def db_client(db_user: AppUser) -> TestClient:
    async def override_current_user() -> AppUser:
        return db_user

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        yield TestClient(app)
    finally:
        async def cleanup() -> None:
            async with SessionLocal() as session:
                await session.execute(delete(UploadSession).where(UploadSession.user_id == db_user.id))
                await session.execute(delete(AppUser).where(AppUser.id == db_user.id))
                await session.commit()

        app.dependency_overrides.pop(get_current_user, None)
        import asyncio

        asyncio.run(cleanup())


def workbook_bytes() -> bytes:
    workbook = Workbook()
    orders = workbook.active
    orders.title = "Orders"
    orders.append(["Order Date", "Revenue"])
    orders.append(["2026-01-01", 100])
    returns = workbook.create_sheet("Returns")
    returns.append(["Reason", "Count"])
    returns.append(["Damaged", 2])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def post_csv(client: TestClient):
    return client.post(
        "/api/v1/upload-sessions",
        files={"file": ("sales.csv", "name,revenue,note\nAman,100,=SUM(A1:A2)\n", "text/csv")},
    )


def test_post_upload_session_with_valid_csv_returns_inspected_session(db_client: TestClient) -> None:
    response = post_csv(db_client)

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "inspected"
    assert data["file_extension"] == "csv"
    assert data["preview_rows"] == [{"name": "Aman", "revenue": "100", "note": "=SUM(A1:A2)"}]
    assert data["detected_columns"][0]["clean_name"] == "name"
    assert any(warning["code"] == "FORMULA_LIKE_VALUES_DETECTED" for warning in data["warnings"])


def test_post_upload_session_with_valid_xlsx_returns_sheet_names(db_client: TestClient) -> None:
    response = db_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("orders.xlsx", workbook_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["sheet_names"] == ["Orders", "Returns"]
    assert data["recommended_sheet_name"] == "Orders"


def test_patch_selected_sheet_name_updates_preview(db_client: TestClient) -> None:
    create_response = db_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("orders.xlsx", workbook_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    upload_session_id = create_response.json()["data"]["id"]

    response = db_client.patch(f"/api/v1/upload-sessions/{upload_session_id}", json={"selected_sheet_name": "Returns"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["selected_sheet_name"] == "Returns"
    assert data["preview_rows"] == [{"Reason": "Damaged", "Count": 2}]


def test_get_upload_session_enforces_ownership(db_client: TestClient, db_user: AppUser) -> None:
    upload_session_id = post_csv(db_client).json()["data"]["id"]
    other_user = AppUser(id=uuid.uuid4(), clerk_user_id=f"user_other_{uuid.uuid4().hex}")

    async def override_current_user() -> AppUser:
        return other_user

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        response = db_client.get(f"/api/v1/upload-sessions/{upload_session_id}")
    finally:
        async def restore_current_user() -> AppUser:
            return db_user

        app.dependency_overrides[get_current_user] = restore_current_user

    assert response.status_code == 404


def test_delete_upload_session_marks_deleted_and_removes_temp_file(db_client: TestClient) -> None:
    settings = get_settings()
    data = post_csv(db_client).json()["data"]
    upload_session_id = data["id"]

    async def get_temp_key() -> str:
        async with SessionLocal() as session:
            upload_session = await session.get(UploadSession, uuid.UUID(upload_session_id))
            assert upload_session is not None
            return upload_session.temp_file_key

    import asyncio

    temp_key = asyncio.run(get_temp_key())
    path = temp_file_path(settings, temp_key)
    assert Path(path).exists()

    response = db_client.delete(f"/api/v1/upload-sessions/{upload_session_id}")

    assert response.status_code == 204
    assert not Path(path).exists()
    assert db_client.get(f"/api/v1/upload-sessions/{upload_session_id}").status_code == 404
