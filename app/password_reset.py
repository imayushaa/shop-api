import hashlib
import secrets
import time

from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import generate_password_hash

from .mail import send_mail

bp = Blueprint("password_reset", __name__)

TOKEN_TTL_SECONDS = 60 * 60
MIN_PASSWORD_LENGTH = 8


def _hash_token(token):
    # Only a hash is stored, so a leaked database does not yield usable tokens.
    return hashlib.sha256(token.encode()).hexdigest()


@bp.post("/reset-request")
def reset_request():
    from . import get_db

    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not isinstance(email, str) or not email:
        return jsonify(error="email required"), 400

    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row is not None:
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        # One live token per user: issuing a new one revokes older ones.
        db.execute("DELETE FROM password_resets WHERE user_id = ?", (row["id"],))
        db.execute(
            "INSERT INTO password_resets (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_hash_token(token), row["id"], now + TOKEN_TTL_SECONDS),
        )
        db.commit()

        template = current_app.config.get("RESET_URL_TEMPLATE")
        link = template.format(token=token) if template else None
        body = (
            "Someone asked to reset the password for this account.\n\n"
            + (f"Reset it here: {link}\n\n" if link else f"Your reset token: {token}\n\n")
            + "This expires in 1 hour. If you didn't ask for this, ignore this email."
        )
        send_mail(email, "Reset your password", body)

    # Same response whether or not the account exists, so this endpoint
    # can't be used to discover registered emails.
    return jsonify(ok=True), 202


@bp.post("/reset")
def reset():
    from . import get_db

    data = request.get_json(silent=True) or {}
    token = data.get("token")
    password = data.get("password")
    if not isinstance(token, str) or not token:
        return jsonify(error="token required"), 400
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return jsonify(error=f"password must be at least {MIN_PASSWORD_LENGTH} characters"), 400

    db = get_db()
    # Consume the token in a single statement so two concurrent requests
    # can't both use it.
    row = db.execute(
        "DELETE FROM password_resets WHERE token_hash = ? AND expires_at > ? RETURNING user_id",
        (_hash_token(token), int(time.time())),
    ).fetchone()
    if row is None:
        db.commit()
        return jsonify(error="invalid or expired token"), 400

    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(password), row["user_id"]),
    )
    db.execute("DELETE FROM password_resets WHERE user_id = ?", (row["user_id"],))
    db.commit()
    return jsonify(ok=True)
