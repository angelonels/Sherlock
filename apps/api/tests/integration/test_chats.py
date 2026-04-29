def test_list_chats_returns_empty_list_for_authenticated_user(authenticated_client):
    response = authenticated_client.get("/api/v1/chats")

    assert response.status_code == 200
    assert response.json() == {"data": [], "pagination": {"next_cursor": None}}

