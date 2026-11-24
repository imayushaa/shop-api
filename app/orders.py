from flask import Blueprint, jsonify, request, session

from .auth import login_required

bp = Blueprint("orders", __name__)

# Column names are interpolated into SQL, so only allowlisted values may be used.
SORTABLE_COLUMNS = {"id", "item", "amount_pence", "created_at"}
DIRECTIONS = {"asc": "ASC", "desc": "DESC"}


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

    query = "SELECT id, item, amount_pence, created_at FROM orders WHERE user_id = ?"

    sort = request.args.get("sort")
    if sort is not None:
        if sort not in SORTABLE_COLUMNS:
            return jsonify(error="bad sort column"), 400
        direction = DIRECTIONS.get(request.args.get("dir", "asc").lower())
        if direction is None:
            return jsonify(error="bad sort direction"), 400
        # id as a tiebreaker keeps ordering stable for equal values.
        query += f" ORDER BY {sort} {direction}, id {direction}"

    rows = get_db().execute(query, (session["user_id"],)).fetchall()
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
