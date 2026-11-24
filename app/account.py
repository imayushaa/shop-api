"""Endpoints for viewing and updating the logged-in user's account."""

from flask import Blueprint, jsonify, request, session
from flask.typing import ResponseReturnValue

from .auth import login_required

bp = Blueprint("account", __name__)


@bp.get("/me")
@login_required
def me() -> ResponseReturnValue:
    """Return the current user's profile.

    Returns:
        A JSON object with ``id``, ``email``, ``display_name`` and
        ``is_admin`` for the user in the session.
    """
    from . import get_db

    row = get_db().execute(
        "SELECT id, email, display_name, is_admin FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    return jsonify(dict(row))


@bp.patch("/me")
@login_required
def update_me() -> ResponseReturnValue:
    """Update columns on the current user's row from the JSON request body.

    Each key in the body is treated as a ``users`` column name and set to
    its value. The ``id`` and ``password_hash`` keys are skipped.

    Returns:
        The updated profile, as returned by :func:`me`.
    """
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
