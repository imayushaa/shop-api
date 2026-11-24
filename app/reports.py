"""Reporting endpoints over the logged-in user's orders."""

from flask import Blueprint, jsonify, request, session
from flask.typing import ResponseReturnValue

from .auth import login_required

bp = Blueprint("reports", __name__)

#: Columns the order report may be sorted by.
SORTABLE_COLUMNS: set[str] = {"created_at", "amount_pence", "item"}
#: Maps the ``dir`` query parameter (lower-cased) to an SQL sort direction.
DIRECTIONS: dict[str, str] = {"asc": "ASC", "desc": "DESC"}


@bp.get("/reports/orders")
@login_required
def order_report() -> ResponseReturnValue:
    """List the current user's orders, sorted as requested.

    Query parameters:
        sort: Column to sort by; one of :data:`SORTABLE_COLUMNS`.
            Defaults to ``created_at``.
        dir: ``asc`` or ``desc`` (case-insensitive). Any other value falls
            back to ``desc``. Defaults to ``desc``.

    Returns:
        A JSON list of orders, each with ``id``, ``item``, ``amount_pence``
        and ``created_at``, or ``{"error": "bad sort column"}`` with status
        400 if ``sort`` is not allowed.
    """
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
