import hashlib
import os
import subprocess
import uuid

from flask import Blueprint, current_app, jsonify, session

from .auth import login_required

bp = Blueprint("exports", __name__)


def cache_key(user_id: int, report: str) -> str:
    return hashlib.md5(f"{user_id}:{report}".encode()).hexdigest()


@bp.post("/exports")
@login_required
def create_export():
    export_dir = current_app.config["EXPORT_DIR"]
    os.makedirs(export_dir, exist_ok=True)

    name = f"{uuid.uuid4().hex}.tar.gz"
    out_path = os.path.join(export_dir, name)
    subprocess.run(
        ["tar", "-czf", out_path, "-C", export_dir, "--files-from", "/dev/null"],
        check=True,
        shell=False,
        timeout=30,
    )
    return jsonify(file=name, cache=cache_key(session["user_id"], "orders")), 201
