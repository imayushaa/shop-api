from flask import Blueprint, jsonify, request, session

from .auth import login_required

bp = Blueprint("reports", __name__)

SORTABLE_COLUMNS = {"created_at", "amount_pence", "item"}
DIRECTIONS = {"asc": "ASC", "desc": "DESC"}


@bp.get("/reports/orders")
@login_required
def order_report():
    from . import get_db

    sort = request.args.get("sort", "created_at")
    direction = DIRECTIONS.get(request.args.get("dir", "desc").lower(), "DESC")
    if sort not in SORTABLE_COLUMNS:
        return jsonify(error="bad sort column"), 400

    query = (
        f"SELECT id, item, amount_pence, created_at FROM orders "
        f"WHERE user_id = ? ORDER BY {sort} {direction}"
    )
    rows = get_db().execute(query, (session["user_id"],)).fetchall()
    return jsonify([dict(r) for r in rows])
