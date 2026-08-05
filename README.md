# Arvion

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
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn arvion.wsgi:application
```

Production requires PostgreSQL, real SMTP credentials and an S3-compatible bucket for uploaded media. Static assets are collected and served through WhiteNoise. The application refuses to start when required production variables are missing or when the sandbox payment gateway is selected.

## Assessment benchmark

The benchmark creates complete 50-question attempts, scores them and rolls every synthetic record back:

```bash
python manage.py benchmark_assessment_engine --attempts 1000
```
