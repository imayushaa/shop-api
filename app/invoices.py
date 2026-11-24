"""Invoice endpoints."""

from flask import Blueprint, jsonify
from flask.typing import ResponseReturnValue

from .auth import login_required

bp = Blueprint("invoices", __name__)


@bp.get("/invoices/<int:invoice_id>")
@login_required
def get_invoice(invoice_id: int) -> ResponseReturnValue:
    """Return a single invoice joined with its order's item and address.

    Args:
        invoice_id: Primary key of the invoice to fetch.

    Returns:
        A JSON object with ``id``, ``total_pence``, ``pdf_path``, ``item`` and
        ``address``, or ``{"error": "not found"}`` with status 404 if no
        invoice has that id.
    """
    from . import get_db

    row = get_db().execute(
        "SELECT i.id, i.total_pence, i.pdf_path, o.item, o.address "
        "FROM invoices i JOIN orders o ON o.id = i.order_id "
        "WHERE i.id = ?",
        (invoice_id,),
    ).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))
