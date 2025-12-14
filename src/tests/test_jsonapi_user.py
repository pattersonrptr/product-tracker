from src.app.interfaces.http.schemas.user_schema import UserCreateRequest, UserAttributes, UserResource

def test_user_create_request_ok():
    attrs = {
        "username": "alice",
        "email": "alice@example.com",
        "is_active": True
    }
    req = UserCreateRequest(
        data=UserResource(type="users", attributes=UserAttributes(**attrs))
    )
    assert req.data.type == "users"
    assert req.data.attributes.username == "alice"
    assert req.data.attributes.email == "alice@example.com"
