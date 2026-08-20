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

## Deployment

Development happens on `dev`. Production runs from `prod`. The local deployment script validates and commits the current work, pushes `dev`, fast-forwards `prod`, then updates the server over SSH.

The production service defaults to `ai-selectora.service`:

```bash
./deploy.sh "Describe this release"
```

If the service name ever changes, override it with `DEPLOY_RESTART_CMD`.

Defaults:

- SSH host: `root@ubuntu-s-1vcpu-512mb-10gb-fra1-01`
- App: `/server/ai.selectora.cc/prod/app`
- Data: `/server/ai.selectora.cc/prod/data`
- Virtualenv: `/server/ai.selectora.cc/prod/venv`
- Restart: `systemctl restart ai-selectora.service`
- Optional environment file: `/server/ai.selectora.cc/prod/.env`
- Production fetch: public read-only HTTPS from `https://github.com/jaumet/ai-disclaimer.git`

Override any of these with `DEPLOY_HOST`, `DEPLOY_REMOTE_APP`, `DEPLOY_REMOTE_DATA`, `DEPLOY_REMOTE_VENV`, or `DEPLOY_REMOTE_ENV`.

Safety checks intentionally stop the deployment when:

- local development is not on `dev`;
- the GitHub remote is unexpected;
- tests or Django checks fail;
- `prod` has diverged from `dev`;
- the server checkout contains tracked local changes or cannot safely switch to `prod`;
- another deployment is running;
- the production virtualenv or expected directories are missing;
- the deployed revision does not exactly match the promoted commit.

Before the first deployment, configure SSH access and the restart command. The script creates the server's local `prod` branch from the explicitly fetched HTTPS ref when needed; no GitHub credentials or tracking upstream are required there. SQLite is backed up into `prod/data/backups/` before migrations.

The local machine pushes to GitHub using its configured SSH credentials. The production server never needs a GitHub password or private key: it fetches the public `prod` branch over read-only HTTPS.
# ai-disclaimer
