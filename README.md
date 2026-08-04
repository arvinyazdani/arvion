# Arvion

Bilingual Django portfolio and lead-generation website.

## Local preview (SQLite)

```bash
./run-local.sh
```

Then open http://127.0.0.1:8000. Local email notifications are printed in the terminal.

## Production (PostgreSQL)

Copy `.env.example` values into the hosting provider, set `DJANGO_SETTINGS_MODULE=arvion.settings.production`, then run:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn arvion.wsgi:application
```

Uploaded media should be persisted by the hosting platform or moved to object storage before launch.
