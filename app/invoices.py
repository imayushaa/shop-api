import os

from flask import Blueprint, current_app, jsonify, send_from_directory, session
from werkzeug.exceptions import NotFound

from .auth import login_required

bp = Blueprint("invoices", __name__)


@bp.get("/invoices/<int:invoice_id>")
@login_required
def get_invoice(invoice_id):
    from . import get_db

    row = get_db().execute(
        "SELECT i.id, i.total_pence, i.pdf_path, o.item, o.address "
        "FROM invoices i JOIN orders o ON o.id = i.order_id "
        "WHERE i.id = ? AND o.user_id = ?",
        (invoice_id, session["user_id"]),
    ).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))


@bp.get("/invoices/<int:invoice_id>/pdf")
@login_required
def get_invoice_pdf(invoice_id):
    from . import get_db

    # Only the owner of the order may download its invoice; anyone else gets
    # the same 404 as a missing invoice so IDs can't be probed.
    row = get_db().execute(
        "SELECT i.pdf_path FROM invoices i JOIN orders o ON o.id = i.order_id "
        "WHERE i.id = ? AND o.user_id = ?",
        (invoice_id, session["user_id"]),
    ).fetchone()
    if row is None:
        return jsonify(error="not found"), 404

    root = os.path.abspath(current_app.config["INVOICE_ROOT"])
    try:
        # send_from_directory refuses paths that escape root.
        return send_from_directory(
            root,
            row["pdf_path"],
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"invoice-{invoice_id}.pdf",
        )
    except NotFound:
        return jsonify(error="invoice file not available"), 404
