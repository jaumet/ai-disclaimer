# AI USE: DECLARED by Selectora

A Django + SQLite registry for transparent disclosure of AI use in websites and digital projects.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/. Sign-in emails use Django's console backend in development, so the one-time link appears in the terminal. It expires after 15 minutes.

## Disclosure rules

Each project has exactly one primary badge and zero or more qualifiers. `NO AI USED` and `NO GENERATIVE AI` may only be paired with `HUMAN-REVIEWED`. Both browser UI and server validation enforce this rule.

Original badge files live in `../ai-logo-system/`; copied web assets under `static/badges/` are derivatives and do not replace the originals.
# ai-disclaimer
