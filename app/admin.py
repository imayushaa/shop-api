from flask import Blueprint, jsonify

from .auth import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/users")
@admin_required
def list_users():
    from . import get_db

    rows = get_db().execute(
        "SELECT id, email, display_name, is_admin FROM users ORDER BY id"
    ).fetchall()
    return jsonify([dict(r) for r in rows])
