import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def isolated_activities(monkeypatch):
    activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(isolated_activities):
    return TestClient(app_module.app)


def signup_url(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def test_root_redirects_to_static_page(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert {"description", "schedule", "max_participants", "participants"} <= set(
        activities["Chess Club"]
    )


def test_signup_adds_participant_and_is_visible_in_activities(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    participants = client.get("/activities").json()[activity_name]["participants"]
    assert email in participants


def test_signup_rejects_duplicate_participant(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate@mergington.edu"
    isolated_activities[activity_name]["participants"].append(email)

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 400
    assert isolated_activities[activity_name]["participants"].count(email) == 1


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(signup_url(activity_name), params={"email": "student@example.edu"})

    # Assert
    assert response.status_code == 404


def test_cancel_signup_removes_participant(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "cancel-me@mergington.edu"
    isolated_activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    participants = client.get("/activities").json()[activity_name]["participants"]
    assert email not in participants


def test_cancel_signup_returns_not_found_for_unregistered_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404


def test_cancel_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(signup_url(activity_name), params={"email": "student@example.edu"})

    # Assert
    assert response.status_code == 404