import os
import sqlite3

from flask import Flask, g

from .auth import bp as auth_bp
from .orders import bp as orders_bp
from .invoices import bp as invoices_bp
from .account import bp as account_bp
from .reports import bp as reports_bp
from .exports import bp as exports_bp
from .password_reset import bp as password_reset_bp

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_admin INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    item TEXT NOT NULL,
    amount_pence INTEGER NOT NULL,
    address TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    pdf_path TEXT NOT NULL,
    total_pence INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS password_resets (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at INTEGER NOT NULL
);
"""


def get_db():
    if "db" not in g:
        from flask import current_app

        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(32)),
        DATABASE=os.environ.get("DATABASE", "shop.db"),
        EXPORT_DIR=os.environ.get("EXPORT_DIR", "exports"),
    )
    if config:
        app.config.update(config)

    app.teardown_appcontext(close_db)
    for bp in (auth_bp, orders_bp, invoices_bp, account_bp, reports_bp, exports_bp, password_reset_bp):
        app.register_blueprint(bp)

    init_db(app)
    return app
