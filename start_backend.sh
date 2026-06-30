#!/bin/bash
cd /home/runner/workspace/Doctrack/asc_doctrack
python3 manage.py migrate --run-syncdb -v 0 2>/dev/null || true
python3 -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
