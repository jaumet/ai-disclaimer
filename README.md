# AI USE DECLARED by Selectora

A Django website for creating anonymous, shareable AI-use declarations and gathering public support for a common badge system. Declaration choices stay in the browser and are never saved; SQLite stores only initiative adhesions. Django users exist solely for internal `/admin/` access.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/. There is no public sign-in or registration flow.

## Disclosure rules

Each declaration has exactly one primary badge and zero or more qualifiers. `NO AI USED` and `NO GENERATIVE AI` may only be paired with `HUMAN-REVIEWED`; the browser interface enforces this rule.

Original badge files live in `../ai-logo-system/`; copied web assets under `static/badges/` are derivatives and do not replace the originals.

## Resend email configuration

Local development uses Django's console email backend by default and does not need a Resend key. Production enables Resend through Django's standard SMTP backend. When SMTP is selected, startup fails clearly if `RESEND_API_KEY` is missing; there is no silent fallback. Never commit `.env` or a real API key.

### Resend sender domain

Complete these manual steps in the same Resend account used by `selectora.cc`:

1. Confirm that the existing sender domain `selectora.cc` still appears as `Verified`. AI Use Declared reuses this verified sender domain, so `ai.selectora.cc` must not be added as a separate Resend domain and no new Cloudflare records are normally required.
2. Create a new, independent API key with:
   - name: `ai.selectora.cc-production`;
   - permission: `Sending access` only;
   - restricted domain: `selectora.cc`.
3. Do not reuse the API key used by the Selectora application.

Official documentation:

- [Add a domain](https://resend.com/docs/add-a-domain)
- [Create an API key](https://resend.com/docs/create-an-api-key)
- [Send with Django SMTP](https://resend.com/docs/send-with-django-smtp)

### Production server

Create the environment file with restricted permissions:

```bash
touch /server/ai.selectora.cc/prod/.env
chown root:root /server/ai.selectora.cc/prod/.env
chmod 600 /server/ai.selectora.cc/prod/.env
vim /server/ai.selectora.cc/prod/.env
```

The administrator must add the following values manually:

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
RESEND_API_KEY=re_REAL_KEY_HERE
DEFAULT_FROM_EMAIL='AI Use Declared <noreply@selectora.cc>'
```

`DEFAULT_FROM_EMAIL` must remain quoted because the production environment file is sourced as a shell script by the deployment process.

Check how the service is configured without printing its environment values:

```bash
systemctl cat ai-selectora.service
```

If the service does not yet load the file, run:

```bash
systemctl edit ai-selectora.service
```

Add:

```ini
[Service]
EnvironmentFile=/server/ai.selectora.cc/prod/.env
```

Then reload and restart it:

```bash
systemctl daemon-reload
systemctl restart ai-selectora.service
systemctl status ai-selectora.service --no-pager
```

Do not use `systemctl show ... -p Environment` or any command that could print the API key.

### Manual delivery test after deployment

Run this only after the domain is verified, the dedicated key is installed and the service loads the environment file:

```bash
cd /server/ai.selectora.cc/prod/app

set -a
. /server/ai.selectora.cc/prod/.env
set +a

/server/ai.selectora.cc/prod/venv/bin/python manage.py shell -c \
'from django.core.mail import send_mail; print(send_mail("AI Use Declared email test", "Resend is configured correctly.", None, ["REPLACE_WITH_TEST_EMAIL"]))'
```

The expected result is `1`. Then verify delivery and inspect the message logs in Resend. Do not run this test with a real address until the production configuration is complete.

Once the domain is verified, the new key is saved in `/server/ai.selectora.cc/prod/.env`, `EnvironmentFile` is active and all local checks pass, deploy through the existing workflow:

```bash
./deploy.sh "Configure Resend email delivery"
```

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
