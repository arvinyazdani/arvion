#!/usr/bin/env sh
set -eu

# Local, non-destructive acceptance gate to run before every release.
if [ -x .venv/bin/python ]; then
    ARVION_PYTHON=.venv/bin/python
else
    ARVION_PYTHON=python
fi

"$ARVION_PYTHON" manage.py check
"$ARVION_PYTHON" manage.py makemigrations --check --dry-run
"$ARVION_PYTHON" manage.py test
"$ARVION_PYTHON" manage.py benchmark_assessment_engine --attempts 100

echo "Arvion release checks passed."
