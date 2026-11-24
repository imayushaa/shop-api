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


def test_owner_can_update_order_address(app):
    alice = make_user(app, "alice@example.com")
    order_id = alice.post(
        "/orders", json={"item": "Laptop", "amount_pence": 99900, "address": "1 Alice St"}
    ).get_json()["id"]

    resp = alice.patch(f"/orders/{order_id}", json={"address": "2 New Rd"})
    assert resp.status_code == 200
    assert resp.get_json()["address"] == "2 New Rd"
    assert alice.get(f"/orders/{order_id}").get_json()["address"] == "2 New Rd"


def test_update_order_address_is_scoped_to_owner(app):
    alice = make_user(app, "alice@example.com")
    bob = make_user(app, "bob@example.com")
    order_id = alice.post(
        "/orders", json={"item": "Laptop", "amount_pence": 99900, "address": "1 Alice St"}
    ).get_json()["id"]

    assert bob.patch(f"/orders/{order_id}", json={"address": "Bob's House"}).status_code == 404
    assert alice.get(f"/orders/{order_id}").get_json()["address"] == "1 Alice St"
    assert app.test_client().patch(f"/orders/{order_id}", json={"address": "x"}).status_code == 401


def test_update_order_address_validates_body(app):
    alice = make_user(app, "alice@example.com")
    order_id = alice.post(
        "/orders", json={"item": "Laptop", "amount_pence": 99900, "address": "1 Alice St"}
    ).get_json()["id"]

    assert alice.patch(f"/orders/{order_id}", json={"address": "   "}).status_code == 400
    assert alice.patch(f"/orders/{order_id}", json={"address": 5}).status_code == 400
    assert alice.patch(f"/orders/{order_id}", json={}).status_code == 400
    assert (
        alice.patch(f"/orders/{order_id}", json={"address": "x", "amount_pence": 1}).status_code
        == 400
    )
    assert alice.patch(f"/orders/{order_id}", data="not json").status_code == 400
