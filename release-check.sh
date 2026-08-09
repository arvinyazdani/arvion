#!/usr/bin/env sh
set -eu

# Local, non-destructive acceptance gate to run before every release.
if [ -x .venv/bin/python ]; then
    RVION_PYTHON=.venv/bin/python
else
    RVION_PYTHON=python
fi

"$RVION_PYTHON" manage.py check
"$RVION_PYTHON" manage.py makemigrations --check --dry-run
"$RVION_PYTHON" -m pip check
"$RVION_PYTHON" manage.py test
"$RVION_PYTHON" manage.py audit_question_banks --strict-editorial
"$RVION_PYTHON" manage.py collectstatic --noinput --dry-run --verbosity 0
"$RVION_PYTHON" manage.py benchmark_assessment_engine --attempts 100

echo "Rvion release checks passed."
