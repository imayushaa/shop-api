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
