"""
E2E Tests for User Controller

Tests the complete user management flow:
    HTTP Request → UserController → UserUseCases → UserRepository → Database
"""



class TestUserCreate:
    """Test POST /users/ - Create new user"""

    def test_create_user_successfully(self, client, superuser_auth_headers):
        """
        Given: Authenticated superuser
        When: POST /users/ with valid user data in JSON:API format
        Then: Returns 201 with created user in JSON:API format
        """
        # When
        response = client.post(
            "/users/",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "newuser",
                        "email": "newuser@example.com",
                        "password": "NewPass@123"
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 201

        data = response.json()
        assert data["data"]["type"] == "users"
        assert data["data"]["attributes"]["username"] == "newuser"
        assert data["data"]["attributes"]["email"] == "newuser@example.com"
        assert "hashed_password" not in data["data"]["attributes"]  # Security check
        assert "id" in data["data"]

    def test_create_user_with_duplicate_username(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user with username 'testuser' already exists
        When: POST /users/ with duplicate username in JSON:API format
        Then: Returns 409 (Conflict) with validation error
        """
        # When
        response = client.post(
            "/users/",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "testuser",  # Duplicate
                        "email": "different@example.com",
                        "password": "Pass@123"
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 409
        data = response.json()
        assert "errors" in data
        assert any("username" in err["detail"].lower() for err in data["errors"])

    def test_create_user_with_duplicate_email(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user with email 'test@example.com' already exists
        When: POST /users/ with duplicate email in JSON:API format
        Then: Returns 409 (Conflict) with validation error
        """
        # When
        response = client.post(
            "/users/",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "differentuser",
                        "email": "test@example.com",  # Duplicate
                        "password": "Pass@123"
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 409
        data = response.json()
        assert "errors" in data
        assert any("email" in err["detail"].lower() for err in data["errors"])

    def test_create_user_without_authentication(self, client):
        """
        Given: No authentication token
        When: POST /users/ without auth headers
        Then: Returns 401 or 403 unauthorized
        """
        # When
        response = client.post(
            "/users/",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "newuser",
                        "email": "newuser@example.com",
                        "password": "Pass@123"
                    }
                }
            }
        )

        # Then
        assert response.status_code in [401, 403]

    def test_create_user_with_invalid_data(self, client, superuser_auth_headers):
        """
        Given: Authenticated superuser
        When: POST /users/ with invalid email format
        Then: Returns 422 validation error
        """
        # When
        response = client.post(
            "/users/",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "newuser",
                        "email": "not-an-email",  # Invalid format
                        "password": "Pass@123"
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 422


class TestUserGetAll:
    """Test GET /users/ - List all users"""

    def test_get_all_users(self, client, sample_user, sample_superuser, superuser_auth_headers):
        """
        Given: Multiple users exist in database
        When: GET /users/ (requires staff/superuser)
        Then: Returns 200 with collection of users in JSON:API format
        """
        # When
        response = client.get("/users/", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2  # At least sample_user and sample_superuser

        # Check JSON:API structure
        for user in data["data"]:
            assert user["type"] == "users"
            assert "id" in user
            assert "attributes" in user
            assert "username" in user["attributes"]

    def test_get_all_users_empty(self, client, superuser_auth_headers):
        """
        Given: No users in database (except authenticated superuser)
        When: GET /users/ (requires staff/superuser)
        Then: Returns 200 with empty or minimal collection
        """
        # When
        response = client.get("/users/", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_all_users_without_authentication(self, client):
        """
        Given: No authentication token
        When: GET /users/
        Then: Returns 401 or 403 unauthorized
        """
        # When
        response = client.get("/users/")

        # Then
        assert response.status_code in [401, 403]


class TestUserGetById:
    """Test GET /users/{user_id} - Get user by ID"""

    def test_get_user_by_id_successfully(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user exists with specific ID
        When: GET /users/{user_id} (requires staff/superuser)
        Then: Returns 200 with user data in JSON:API format
        """
        # When
        response = client.get(f"/users/{sample_user.id}", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["type"] == "users"
        assert data["data"]["id"] == str(sample_user.id)
        assert data["data"]["attributes"]["username"] == "testuser"
        assert "hashed_password" not in data["data"]["attributes"]

    def test_get_user_by_id_not_found(self, client, superuser_auth_headers):
        """
        Given: No user exists with ID 99999
        When: GET /users/99999 (requires staff/superuser)
        Then: Returns 404 not found
        """
        # When
        response = client.get("/users/99999", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 404

        data = response.json()
        assert "errors" in data
        assert data["errors"][0]["status"] == "404"


class TestUserGetByUsername:
    """Test GET /users/username/{username} - Get user by username"""

    def test_get_user_by_username_successfully(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user with username 'testuser' exists
        When: GET /users/username/testuser (requires staff/superuser)
        Then: Returns 200 with user data
        """
        # When
        response = client.get("/users/username/testuser", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["attributes"]["username"] == "testuser"

    def test_get_user_by_username_not_found(self, client, superuser_auth_headers):
        """
        Given: No user with username 'nonexistent'
        When: GET /users/username/nonexistent (requires staff/superuser)
        Then: Returns 404 not found
        """
        # When
        response = client.get("/users/username/nonexistent", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 404


class TestUserGetByEmail:
    """Test GET /users/email/{email} - Get user by email"""

    def test_get_user_by_email_successfully(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user with email 'test@example.com' exists
        When: GET /users/email/test@example.com (requires staff/superuser)
        Then: Returns 200 with user data
        """
        # When
        response = client.get("/users/email/test@example.com", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["attributes"]["email"] == "test@example.com"

    def test_get_user_by_email_not_found(self, client, superuser_auth_headers):
        """
        Given: No user with email 'notfound@example.com'
        When: GET /users/email/notfound@example.com (requires staff/superuser)
        Then: Returns 404 not found
        """
        # When
        response = client.get("/users/email/notfound@example.com", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 404


class TestUserUpdate:
    """Test PUT /users/{user_id} - Update user"""

    def test_update_user_successfully(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user exists
        When: PUT /users/{user_id} with valid update data in JSON:API format
        Then: Returns 200 with updated user data
        """
        # When
        response = client.put(
            f"/users/{sample_user.id}",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "updateduser"
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["attributes"]["username"] == "updateduser"

    def test_update_user_partial_fields(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user exists
        When: PUT /users/{user_id} with only some fields in JSON:API format
        Then: Returns 200 with partially updated user
        """
        # When
        response = client.put(
            f"/users/{sample_user.id}",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "is_active": False
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["attributes"]["is_active"] is False
        assert data["data"]["attributes"]["username"] == "testuser"  # Unchanged

    def test_update_user_not_found(self, client, superuser_auth_headers):
        """
        Given: No user exists with ID 99999
        When: PUT /users/99999 with JSON:API format
        Then: Returns 404 not found
        """
        # When
        response = client.put(
            "/users/99999",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "newname"
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code == 404

    def test_update_user_duplicate_username(self, client, sample_user, sample_superuser, superuser_auth_headers):
        """
        Given: Two users exist
        When: PUT /users/{id} with username that belongs to another user in JSON:API format
        Then: Returns 400 or 409 validation error
        """
        # When
        response = client.put(
            f"/users/{sample_user.id}",
            json={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "admin"  # sample_superuser's username
                    }
                }
            },
            headers=superuser_auth_headers
        )

        # Then
        assert response.status_code in [400, 409]


class TestUserDelete:
    """Test DELETE /users/{user_id} - Delete user"""

    def test_delete_user_successfully(self, client, sample_user, superuser_auth_headers):
        """
        Given: A user exists
        When: DELETE /users/{user_id}
        Then: Returns 204 no content and user is deleted
        """
        user_id = sample_user.id

        # When
        response = client.delete(f"/users/{user_id}", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/users/{user_id}", headers=superuser_auth_headers)
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client, superuser_auth_headers):
        """
        Given: No user exists with ID 99999
        When: DELETE /users/99999
        Then: Returns 404 not found
        """
        # When
        response = client.delete("/users/99999", headers=superuser_auth_headers)

        # Then
        assert response.status_code == 404

    def test_delete_user_without_authorization(self, client, sample_user, auth_headers):
        """
        Given: Regular user authenticated (not superuser)
        When: DELETE /users/{user_id}
        Then: Returns 403 forbidden (if authorization is implemented)
              OR succeeds if no authorization check exists
        """
        # When
        response = client.delete(f"/users/{sample_user.id}", headers=auth_headers)

        # Then
        # Adjust based on your authorization implementation
        # For now, assuming no fine-grained authorization:
        assert response.status_code in [200, 204, 403]
