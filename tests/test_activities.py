"""
Tests for Mergington High School Activities API

This module contains comprehensive tests for all API endpoints using the AAA (Arrange-Act-Assert) pattern.
Tests cover happy-path scenarios and edge cases for all endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestActivitiesAPI:
    """Test suite for the Activities API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_get_activities_success(self, client):
        """Test GET /activities returns all activities successfully."""
        # Arrange - Set up test client

        # Act - Make request to get activities
        response = client.get("/activities")

        # Assert - Verify response
        assert response.status_code == 200
        activities = response.json()

        # Verify response structure
        assert isinstance(activities, dict)
        assert len(activities) > 0

        # Verify each activity has required fields
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_root_redirect(self, client):
        """Test GET / redirects to static frontend."""
        # Arrange - Set up test client

        # Act - Make request to root endpoint (don't follow redirects)
        response = client.get("/", follow_redirects=False)

        # Assert - Verify redirect
        assert response.status_code in [301, 307, 308]  # Common redirect codes
        assert "/static/index.html" in response.headers.get("location", "")

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        # Arrange - Set up test data
        activity_name = "Chess Club"
        email = "test@mergington.edu"

        # Act - Make signup request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert - Verify success
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert activity_name in result["message"]
        assert email in result["message"]

        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup fails when activity doesn't exist."""
        # Arrange - Set up test data with non-existent activity
        activity_name = "NonExistentActivity"
        email = "test@mergington.edu"

        # Act - Make signup request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert - Verify error response
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()

    def test_signup_duplicate_email(self, client):
        """Test signup fails when email is already registered."""
        # Arrange - Set up test data
        activity_name = "Chess Club"
        email = "duplicate@mergington.edu"

        # First signup (should succeed)
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Act - Try to signup again with same email
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert - Verify error response
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"].lower()

    def test_unregister_success(self, client):
        """Test successful unregister from an activity."""
        # Arrange - Set up test data
        activity_name = "Programming Class"
        email = "unregister_test@mergington.edu"

        # First signup the participant
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Act - Make unregister request
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert - Verify success
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert activity_name in result["message"]
        assert email in result["message"]

        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister fails when activity doesn't exist."""
        # Arrange - Set up test data with non-existent activity
        activity_name = "NonExistentActivity"
        email = "test@mergington.edu"

        # Act - Make unregister request
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert - Verify error response
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()

    def test_unregister_email_not_found(self, client):
        """Test unregister fails when email is not registered for activity."""
        # Arrange - Set up test data
        activity_name = "Gym Class"
        email = "not_registered@mergington.edu"

        # Act - Try to unregister email that's not in the activity
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert - Verify error response
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()

    def test_signup_unregister_roundtrip(self, client):
        """Test complete signup and unregister cycle."""
        # Arrange - Set up test data
        activity_name = "Basketball Team"
        email = "roundtrip@mergington.edu"

        # Act & Assert - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Verify added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

        # Act & Assert - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Verify removed
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]

    def test_activities_data_integrity(self, client):
        """Test that activity data structure remains consistent."""
        # Arrange - Set up test client

        # Act - Get activities
        response = client.get("/activities")

        # Assert - Verify data integrity
        assert response.status_code == 200
        activities = response.json()

        # Check that all activities have consistent structure
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

            # Verify max_participants is reasonable
            assert activity_data["max_participants"] > 0

            # Verify all participants are strings (emails)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email format check