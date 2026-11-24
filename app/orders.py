from flask import Blueprint, jsonify, request, session

from .auth import login_required

bp = Blueprint("orders", __name__)


@bp.post("/orders")
@login_required
def create_order():
    from . import get_db

    data = request.get_json(force=True)
    db = get_db()
    cur = db.execute(
        "INSERT INTO orders (user_id, item, amount_pence, address) VALUES (?, ?, ?, ?)",
        (session["user_id"], data["item"], int(data["amount_pence"]), data["address"]),
    )
    order_id = cur.lastrowid
    db.execute(
        "INSERT INTO invoices (order_id, pdf_path, total_pence) VALUES (?, ?, ?)",
        (order_id, f"invoices/{order_id}.pdf", int(data["amount_pence"])),
    )
    db.commit()
    return jsonify(id=order_id), 201


@bp.get("/orders")
@login_required
def list_orders():
    from . import get_db

    rows = get_db().execute(
        "SELECT id, item, amount_pence, created_at FROM orders WHERE user_id = ?",
        (session["user_id"],),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    from . import get_db

    row = get_db().execute(
        "SELECT id, item, amount_pence, address, created_at FROM orders "
        "WHERE id = ? AND user_id = ?",
        (order_id, session["user_id"]),
    ).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@bp.patch("/orders/<int:order_id>")
@login_required
def update_order_address(order_id):
    from . import get_db

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {"address"}:
        return jsonify(error="body must be a JSON object with only 'address'"), 400
    address = data["address"]
    if not isinstance(address, str) or not address.strip():
        return jsonify(error="address must be a non-empty string"), 400

    db = get_db()
    cur = db.execute(
        "UPDATE orders SET address = ? WHERE id = ? AND user_id = ?",
        (address.strip(), order_id, session["user_id"]),
    )
    if cur.rowcount == 0:
        return jsonify(error="not found"), 404
    db.commit()

    row = db.execute(
        "SELECT id, item, amount_pence, address, created_at FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    return jsonify(dict(row))
