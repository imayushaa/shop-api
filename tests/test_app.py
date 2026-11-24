import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only",
            "DATABASE": str(tmp_path / "test.db"),
            "EXPORT_DIR": str(tmp_path / "exports"),
        }
    )


def make_user(app, email, password="password123"):
    client = app.test_client()
    client.post("/register", json={"email": email, "password": password})
    assert client.post("/login", json={"email": email, "password": password}).status_code == 200
    return client


def test_orders_are_scoped_to_owner(app):
    alice = make_user(app, "alice@example.com")
    bob = make_user(app, "bob@example.com")
    order_id = alice.post(
        "/orders", json={"item": "Laptop", "amount_pence": 99900, "address": "1 Alice St"}
    ).get_json()["id"]

    assert alice.get(f"/orders/{order_id}").status_code == 200
    assert bob.get(f"/orders/{order_id}").status_code == 404


def test_report_sort_rejects_unknown_columns(app):
    alice = make_user(app, "alice@example.com")
    assert alice.get("/reports/orders?sort=created_at&dir=asc").status_code == 200
    assert alice.get("/reports/orders?sort=id;DROP TABLE users").status_code == 400


def test_export_runs(app):
    alice = make_user(app, "alice@example.com")
    assert alice.post("/exports").status_code == 201


def _capture_mail(app):
    sent = []
    app.config["MAIL_SEND"] = lambda to, subject, body: sent.append((to, subject, body))
    return sent


def _token_from(body):
    return body.split("Your reset token: ")[1].split()[0]


def test_password_reset_flow(app):
    sent = _capture_mail(app)
    make_user(app, "alice@example.com", "old-password")
    client = app.test_client()

    assert client.post("/reset-request", json={"email": "alice@example.com"}).status_code == 202
    assert len(sent) == 1 and sent[0][0] == "alice@example.com"
    token = _token_from(sent[0][2])

    assert client.post("/reset", json={"token": token, "password": "short"}).status_code == 400
    assert client.post("/reset", json={"token": token, "password": "new-password"}).status_code == 200

    assert client.post("/login", json={"email": "alice@example.com", "password": "old-password"}).status_code == 401
    assert client.post("/login", json={"email": "alice@example.com", "password": "new-password"}).status_code == 200

    # Tokens are single-use.
    assert client.post("/reset", json={"token": token, "password": "another-pass"}).status_code == 400


def test_password_reset_request_does_not_reveal_accounts(app):
    sent = _capture_mail(app)
    resp = app.test_client().post("/reset-request", json={"email": "nobody@example.com"})
    assert resp.status_code == 202
    assert resp.get_json() == {"ok": True}
    assert sent == []


def test_password_reset_new_request_revokes_old_token(app):
    sent = _capture_mail(app)
    make_user(app, "alice@example.com")
    client = app.test_client()
    client.post("/reset-request", json={"email": "alice@example.com"})
    client.post("/reset-request", json={"email": "alice@example.com"})
    old, new = _token_from(sent[0][2]), _token_from(sent[1][2])

    assert client.post("/reset", json={"token": old, "password": "new-password"}).status_code == 400
    assert client.post("/reset", json={"token": new, "password": "new-password"}).status_code == 200


def test_password_reset_token_expires(app, monkeypatch):
    import time

    sent = _capture_mail(app)
    make_user(app, "alice@example.com")
    client = app.test_client()
    client.post("/reset-request", json={"email": "alice@example.com"})
    token = _token_from(sent[0][2])

    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 2 * 60 * 60)
    assert client.post("/reset", json={"token": token, "password": "new-password"}).status_code == 400
