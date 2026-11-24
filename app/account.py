from flask import Blueprint, jsonify, request, session

from .auth import login_required

bp = Blueprint("account", __name__)

# Fields a user may change on their own account. Never include is_admin.
EDITABLE_FIELDS = {"display_name"}


@bp.get("/me")
@login_required
def me():
    from . import get_db

    row = get_db().execute(
        "SELECT id, email, display_name, is_admin FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    return jsonify(dict(row))


@bp.patch("/me")
@login_required
def update_me():
    from . import get_db

    data = request.get_json(force=True)
    if not isinstance(data, dict):
        return jsonify(error="expected a JSON object"), 400
    unknown = set(data) - EDITABLE_FIELDS
    if unknown:
        return jsonify(error="fields not editable", fields=sorted(unknown)), 400

    db = get_db()
    if "display_name" in data:
        db.execute(
            "UPDATE users SET display_name = ? WHERE id = ?",
            (data["display_name"], session["user_id"]),
        )
    db.commit()
    return me()
