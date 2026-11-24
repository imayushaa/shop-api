from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="login required"), 401
        return view(*args, **kwargs)

    return wrapped


@bp.post("/register")
def register():
    from . import get_db

    data = request.get_json(force=True)
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
        (data["email"], generate_password_hash(data["password"]), data.get("display_name")),
    )
    db.commit()
    return jsonify(id=cur.lastrowid), 201


@bp.post("/login")
def login():
    from . import get_db

    data = request.get_json(force=True)
    row = get_db().execute(
        "SELECT id, password_hash FROM users WHERE email = ?", (data["email"],)
    ).fetchone()
    if row is None or not check_password_hash(row["password_hash"], data["password"]):
        return jsonify(error="invalid credentials"), 401
    session.clear()
    session["user_id"] = row["id"]
    return jsonify(ok=True)


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)
