# shop-api

Small Flask + SQLite shop backend with packaging scripts and Terraform for its infrastructure.

## Run

```bash
pip install -r requirements.txt
flask --app "app:create_app()" run
```

## Test

```bash
pytest -q
```

## Layout

- `app/` – API (auth, orders, invoices, account, reports, exports)
- `packaging/` – agent install scripts (online and air-gapped)
- `infra/` – Route 53 + S3 + CloudFront Terraform

## Password reset

- `POST /reset-request` `{"email": ...}` → always `202`; if the account exists, emails a single-use token valid for 1 hour.
- `POST /reset` `{"token": ..., "password": ...}` → sets the new password (min 8 chars).

Email config: `MAIL_SERVER`, `MAIL_PORT` (587), `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS` (true), `MAIL_FROM`.
Set `RESET_URL_TEMPLATE` (e.g. `https://shop.example/reset?token={token}`) to email a link instead of a raw token.
