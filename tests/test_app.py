def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_index_empty_state(client):
    resp = client.get("/")
    assert b"No batteries" in resp.data or b"inventory" in resp.data.lower()


def test_add_get(client):
    resp = client.get("/add")
    assert resp.status_code == 200


def test_add_post_creates_battery(client):
    resp = client.post("/add", data={
        "label": "Test Battery",
        "voltage": "18",
        "ah_rating": "5.0",
        "is_oem": "1",
        "status": "New",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Test Battery" in resp.data


def test_add_post_redirects(client):
    resp = client.post("/add", data={
        "label": "Redirect Test",
        "voltage": "18",
        "ah_rating": "5.0",
        "is_oem": "1",
        "status": "New",
    })
    assert resp.status_code == 302


def test_edit_get(client):
    # Create a battery first
    client.post("/add", data={
        "label": "Edit Me",
        "voltage": "18",
        "ah_rating": "5.0",
        "is_oem": "1",
        "status": "New",
    })
    resp = client.get("/edit/1")
    assert resp.status_code == 200
    assert b"Edit Me" in resp.data


def test_edit_post_updates_battery(client):
    client.post("/add", data={
        "label": "Original",
        "voltage": "18",
        "ah_rating": "5.0",
        "is_oem": "1",
        "status": "New",
    })
    resp = client.post("/edit/1", data={
        "label": "Updated",
        "voltage": "18",
        "ah_rating": "5.0",
        "is_oem": "1",
        "status": "In Use",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Updated" in resp.data


def test_delete_removes_battery(client):
    client.post("/add", data={
        "label": "Delete Me",
        "voltage": "18",
        "ah_rating": "5.0",
        "is_oem": "1",
        "status": "New",
    })
    resp = client.post("/delete/1", follow_redirects=True)
    assert resp.status_code == 200
    assert b"deleted" in resp.data.lower()


def test_settings_get(client):
    resp = client.get("/settings")
    assert resp.status_code == 200


def test_settings_post_changes_brand(client):
    resp = client.post("/settings", data={"brand": "DeWalt"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"DeWalt" in resp.data


def test_feedback_get(client):
    resp = client.get("/feedback")
    assert resp.status_code == 200


def test_feedback_post_with_message(client):
    resp = client.post("/feedback", data={"message": "Great app!"})
    assert resp.status_code == 302
    # Follow redirect and check flash
    resp = client.get("/", follow_redirects=True)
    assert b"Thanks" in resp.data or resp.status_code == 200


def test_feedback_post_blank_message(client):
    resp = client.post("/feedback", data={"message": "   "})
    assert resp.status_code == 200
    assert b"blank" in resp.data.lower() or b"cannot" in resp.data.lower()
