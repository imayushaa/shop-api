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
