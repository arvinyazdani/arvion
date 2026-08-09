# Rvion

Bilingual Django portfolio and lead-generation website.

## Local preview (SQLite)

```bash
./run-local.sh
```

Then open http://127.0.0.1:8000. Local email notifications are printed in the terminal.

If port 8000 is already used, run `./run-local.sh 8001` or `python manage.py runserver 127.0.0.1:8001`.

## Production (PostgreSQL)

Copy `.env.example` values into the hosting provider, set `DJANGO_SETTINGS_MODULE=arvion.settings.production`, then run:

```bash
./deploy.sh
gunicorn arvion.wsgi:application
```

`deploy.sh` updates the PostgreSQL schema, publishes both validated 200-question assessment banks, and collects static files. It is safe to run again during later deployments: published bank versions are not duplicated, and user accounts, orders, attempts, and results are never seeded or deleted.

The deployment also creates four least-privilege admin roles: `sales`, `assessments`, `support`, and `content`. Create the staff member as a normal user, then assign exactly one operational role without granting superuser access:

```bash
python manage.py setup_staff_roles --email staff@example.com --role sales
```

Use a superuser only for the company owner. Re-running the command is safe and preserves unrelated custom groups.

Production requires PostgreSQL, real SMTP credentials and an S3-compatible bucket for uploaded media. Static assets are collected and served through WhiteNoise. The application refuses to start when required production variables are missing or when the sandbox payment gateway is selected.

Before each release, run the non-destructive acceptance gate locally:

```bash
./release-check.sh
```

Project architecture, delivery history and current blockers are maintained in `PROJECT_STATUS.md`. Use `FINAL_RELEASE_CHECKLIST.md` for the staging and go-live handoff, `QUESTION_BANK_AUDIT.md` for assessment quality boundaries and `CRM_DISCOVERY_GUIDE.md` for the enterprise CRM intake rationale.

After deployment, configure the platform health probe to request `GET /health/`. A healthy instance returns HTTP 200 with `{"status":"ok"}`; loss of database connectivity returns HTTP 503 without exposing internal errors.

Deployment checklist:

- provision PostgreSQL with backups and a TLS connection URL;
- create a unique random `DJANGO_SECRET_KEY` of at least 50 characters;
- configure the public hosts and HTTPS CSRF origins;
- connect real SMTP and verify the sender domain;
- create the private S3-compatible media bucket and its public/custom media domain;
- connect and test a real payment provider callback before accepting paid orders;
- run `./deploy.sh`, start Gunicorn, and verify `/health/`;
- test registration, email verification, payment, one complete assessment, result email, certificate and support from the public domain.

## Assessment benchmark

The benchmark creates complete 50-question attempts, scores them and rolls every synthetic record back:

```bash
python manage.py benchmark_assessment_engine --attempts 1000
```
## Payment gateway integration contract

Local development uses the 100% discount checkout and production always disables it. To connect a real provider, set `PAYMENT_GATEWAY` to a stable lowercase provider name and implement provider-specific initiation and callback views. The callback must verify the transaction directly with the provider before calling:

```python
verify_gateway_payment(
    order_id,
    gateway="provider-name",
    external_id=provider_transaction_id,
    amount_irr=provider_verified_amount,
    response=safe_provider_metadata,
)
```

Never trust an amount, status, or transaction ID sent only by the browser. The service locks the order, requires prior acceptance of the assessment terms, checks the configured gateway and exact IRR amount, rejects cross-order transaction replay, strips common secrets from audit metadata, and creates at most one entitlement. Provider credentials must stay in environment variables and must never be passed in `response`.

Production refuses the `sandbox` gateway. Before deployment, add the selected provider's SDK/client, signed callback validation, server-to-server verification, callback URL, credentials, and provider-specific automated tests.
