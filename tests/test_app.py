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
            "INVOICE_ROOT": str(tmp_path),
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


def test_invoice_pdf_download(app, tmp_path):
    alice = make_user(app, "alice@example.com")
    bob = make_user(app, "bob@example.com")
    order_id = alice.post(
        "/orders", json={"item": "Laptop", "amount_pence": 99900, "address": "1 Alice St"}
    ).get_json()["id"]
    invoice_id = order_id  # one invoice is created per order

    # No file on disk yet.
    assert alice.get(f"/invoices/{invoice_id}/pdf").status_code == 404

    pdf_bytes = b"%PDF-1.4 test invoice"
    (tmp_path / "invoices").mkdir()
    (tmp_path / "invoices" / f"{order_id}.pdf").write_bytes(pdf_bytes)

    resp = alice.get(f"/invoices/{invoice_id}/pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data == pdf_bytes
    assert "attachment" in resp.headers["Content-Disposition"]
    assert f"invoice-{invoice_id}.pdf" in resp.headers["Content-Disposition"]

    assert bob.get(f"/invoices/{invoice_id}/pdf").status_code == 404
    assert alice.get("/invoices/9999/pdf").status_code == 404
    assert app.test_client().get(f"/invoices/{invoice_id}/pdf").status_code == 401
