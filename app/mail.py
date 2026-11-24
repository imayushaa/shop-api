import smtplib
from email.message import EmailMessage

from flask import current_app


def send_mail(to, subject, body):
    """Send a plain-text email.

    Uses ``app.config["MAIL_SEND"]`` (a callable ``(to, subject, body)``) when
    set, which is how tests capture outgoing mail. Otherwise sends over SMTP
    using ``MAIL_SERVER``/``MAIL_PORT``/``MAIL_USERNAME``/``MAIL_PASSWORD``/
    ``MAIL_USE_TLS``/``MAIL_FROM``.
    """
    cfg = current_app.config
    override = cfg.get("MAIL_SEND")
    if override is not None:
        override(to, subject, body)
        return

    server = cfg.get("MAIL_SERVER")
    if not server:
        # Never log the body: it may contain a secret such as a reset token.
        current_app.logger.warning("MAIL_SERVER not configured; email not sent")
        return

    msg = EmailMessage()
    msg["From"] = cfg.get("MAIL_FROM", "no-reply@localhost")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(server, int(cfg.get("MAIL_PORT", 587)), timeout=10) as smtp:
        if cfg.get("MAIL_USE_TLS", True):
            smtp.starttls()
        if cfg.get("MAIL_USERNAME"):
            smtp.login(cfg["MAIL_USERNAME"], cfg.get("MAIL_PASSWORD", ""))
        smtp.send_message(msg)
