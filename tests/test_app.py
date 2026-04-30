import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset in-memory activity state before every test."""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    })
    yield
    activities.clear()


class TestRoot:
    def test_redirect_to_index_html(self):
        # Arrange
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location


class TestGetActivities:
    def test_get_all_activities(self):
        # Arrange
        expected_activity = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert expected_activity in data

    def test_activity_structure(self):
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data[activity_name]

        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    def test_successful_signup(self):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        url = f"/activities/{activity_name}/signup"

        # Act
        response = client.post(url, params={"email": email})

        # Assert
        assert response.status_code == 200
        assert f"Signed up {email} for {activity_name}" in response.json()["message"]
        assert email in activities[activity_name]["participants"]

    def test_signup_nonexistent_activity(self):
        # Arrange
        invalid_activity = "Fake Activity"
        email = "student@mergington.edu"
        url = f"/activities/{invalid_activity}/signup"

        # Act
        response = client.post(url, params={"email": email})

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_enrollment(self):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        url = f"/activities/{activity_name}/signup"

        # Act
        response = client.post(url, params={"email": existing_email})

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestRemoveParticipant:
    def test_successful_removal(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        url = f"/activities/{activity_name}/participants/{email}"

        # Act
        response = client.delete(url)

        # Assert
        assert response.status_code == 200
        assert f"Removed {email} from {activity_name}" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]

    def test_remove_nonexistent_activity(self):
        # Arrange
        invalid_activity = "Fake Activity"
        email = "student@mergington.edu"
        url = f"/activities/{invalid_activity}/participants/{email}"

        # Act
        response = client.delete(url)

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_non_participant(self):
        # Arrange
        activity_name = "Chess Club"
        non_participant_email = "notmember@mergington.edu"
        url = f"/activities/{activity_name}/participants/{non_participant_email}"

        # Act
        response = client.delete(url)

        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]


class TestIntegration:
    def test_signup_and_retrieve(self):
        # Arrange
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        signup_url = f"/activities/{activity_name}/signup"

        # Act
        client.post(signup_url, params={"email": email})
        response = client.get("/activities")

        # Assert
        assert email in response.json()[activity_name]["participants"]

    def test_signup_and_remove(self):
        # Arrange
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        signup_url = f"/activities/{activity_name}/signup"
        delete_url = f"/activities/{activity_name}/participants/{email}"

        # Act
        client.post(signup_url, params={"email": email})
        client.delete(delete_url)
        response = client.get("/activities")

        # Assert
        assert email not in response.json()[activity_name]["participants"]
