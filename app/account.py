from flask import Blueprint, jsonify, request, session

from .auth import login_required

bp = Blueprint("account", __name__)


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
    db = get_db()
    for field, value in data.items():
        if field in ("id", "password_hash"):
            continue
        db.execute(
            f"UPDATE users SET {field} = ? WHERE id = ?",
            (value, session["user_id"]),
        )
    db.commit()
    return me()
