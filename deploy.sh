#!/usr/bin/env bash
set -Eeuo pipefail

# AI USE: DECLARED deployment: local dev -> GitHub prod -> production server.
# Usage:
#   ./deploy.sh "Commit message"

readonly EXPECTED_BRANCH="dev"
readonly EXPECTED_REPOSITORY="jaumet/ai-disclaimer"
readonly DEPLOY_HOST="${DEPLOY_HOST:-phab}"
readonly REMOTE_APP="${DEPLOY_REMOTE_APP:-/server/ai.selectora.cc/prod/app}"
readonly REMOTE_DATA="${DEPLOY_REMOTE_DATA:-/server/ai.selectora.cc/prod/data}"
readonly REMOTE_VENV="${DEPLOY_REMOTE_VENV:-/server/ai.selectora.cc/prod/venv}"
readonly REMOTE_ENV="${DEPLOY_REMOTE_ENV:-/server/ai.selectora.cc/prod/.env}"
readonly RESTART_CMD="${DEPLOY_RESTART_CMD:-systemctl restart ai-selectora.service}"
readonly COMMIT_MESSAGE="${1:-}"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
step() { printf '\n==> %s\n' "$*"; }

[[ -n "$COMMIT_MESSAGE" ]] || fail 'Pass a commit message: ./deploy.sh "Describe the release"'
for command_name in git ssh; do
    command -v "$command_name" >/dev/null || fail "Missing required command: $command_name"
done

readonly REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || fail 'Run this inside the Git repository.'
cd "$REPO_ROOT"

readonly CURRENT_BRANCH="$(git branch --show-current)"
[[ "$CURRENT_BRANCH" == "$EXPECTED_BRANCH" ]] || fail "Current branch is '$CURRENT_BRANCH'; switch to '$EXPECTED_BRANCH' first."

readonly ORIGIN_URL="$(git remote get-url origin)"
case "$ORIGIN_URL" in
    *github.com/jaumet/ai-disclaimer.git|git@github.com:jaumet/ai-disclaimer.git) ;;
    *) fail "Unexpected origin: $ORIGIN_URL" ;;
esac

step 'Running local validation'
[[ -x .venv/bin/python ]] || fail 'Local .venv is missing. Create it and install requirements first.'
.venv/bin/python manage.py test
.venv/bin/python manage.py check
bash -n deploy.sh
if command -v shellcheck >/dev/null; then shellcheck deploy.sh; fi
git diff --check

step 'Reviewing local changes'
git status --short --branch
git diff --stat
git diff --cached --stat

if [[ -n "$(git status --porcelain)" ]]; then
    printf '\nThese changes will be committed to dev and deployed to production.\n'
    read -r -p 'Continue? [y/N] ' confirmation
    [[ "$confirmation" =~ ^[Yy]$ ]] || fail 'Deployment cancelled.'
    git add -A
    git diff --cached --check
    git commit -m "$COMMIT_MESSAGE"
else
    printf 'No local changes; deploying the current dev commit.\n'
    read -r -p 'Continue? [y/N] ' confirmation
    [[ "$confirmation" =~ ^[Yy]$ ]] || fail 'Deployment cancelled.'
fi

step 'Pushing dev to GitHub'
git push origin dev
git fetch origin --prune

step 'Promoting dev to prod with fast-forward protection'
if git show-ref --verify --quiet refs/remotes/origin/prod; then
    git merge-base --is-ancestor origin/prod dev || fail 'origin/prod has diverged from dev. Resolve it manually; nothing was overwritten.'
fi
git push origin dev:prod

readonly RELEASE_REV="$(git rev-parse HEAD)"
step "Deploying $RELEASE_REV to $DEPLOY_HOST"

ssh "$DEPLOY_HOST" bash -s -- \
    "$REMOTE_APP" "$REMOTE_DATA" "$REMOTE_VENV" "$REMOTE_ENV" "$RESTART_CMD" "$RELEASE_REV" <<'REMOTE_SCRIPT'
set -Eeuo pipefail

readonly APP_DIR="$1"
readonly DATA_DIR="$2"
readonly VENV_DIR="$3"
readonly ENV_FILE="$4"
readonly RESTART_CMD="$5"
readonly EXPECTED_REV="$6"
readonly LOCK_DIR="${APP_DIR%/}/../.deploy-lock"

remote_fail() { printf 'REMOTE ERROR: %s\n' "$*" >&2; exit 1; }
remote_step() { printf '\n--> %s\n' "$*"; }
cleanup() { rmdir "$LOCK_DIR" 2>/dev/null || true; }

[[ "$APP_DIR" == "/server/ai.selectora.cc/prod/app" ]] || remote_fail "Unexpected app path: $APP_DIR"
[[ -d "$APP_DIR" && ! -L "$APP_DIR" ]] || remote_fail 'App directory is missing or is a symbolic link.'
[[ -d "$DATA_DIR" && ! -L "$DATA_DIR" ]] || remote_fail 'Data directory is missing or is a symbolic link.'
[[ -x "$VENV_DIR/bin/python" && -x "$VENV_DIR/bin/pip" ]] || remote_fail 'Production virtualenv is incomplete.'
mkdir "$LOCK_DIR" 2>/dev/null || remote_fail 'Another deployment appears to be running.'
trap cleanup EXIT

cd "$APP_DIR"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || remote_fail 'App is not a Git checkout.'
git diff --quiet && git diff --cached --quiet || remote_fail 'Server checkout has tracked local changes. Refusing to overwrite them.'

remote_step 'Preparing the production branch'
git fetch origin prod
if [[ "$(git branch --show-current)" != "prod" ]]; then
    if git show-ref --verify --quiet refs/heads/prod; then
        git switch prod
    else
        git switch --track -c prod origin/prod
    fi
fi
[[ "$(git branch --show-current)" == "prod" ]] || remote_fail "Could not switch the server checkout to 'prod'."
git diff --quiet && git diff --cached --quiet || remote_fail 'Production branch has tracked local changes.'

if [[ -f "$ENV_FILE" ]]; then
    remote_step "Loading environment from $ENV_FILE"
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

remote_step 'Backing up SQLite'
readonly BACKUP_DIR="$DATA_DIR/backups"
mkdir -p "$BACKUP_DIR"
if [[ -f "$DATA_DIR/db.sqlite3" && ! -L "$DATA_DIR/db.sqlite3" ]]; then
    cp -p "$DATA_DIR/db.sqlite3" "$BACKUP_DIR/db-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
elif [[ -f "$APP_DIR/db.sqlite3" && ! -L "$APP_DIR/db.sqlite3" ]]; then
    cp -p "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
else
    printf 'No SQLite database found to back up.\n'
fi

remote_step 'Updating production code'
git merge --ff-only origin/prod
[[ "$(git rev-parse HEAD)" == "$EXPECTED_REV" ]] || remote_fail 'Server revision does not match the promoted release.'

remote_step 'Installing dependencies'
"$VENV_DIR/bin/pip" install --disable-pip-version-check -r requirements.txt

remote_step 'Applying database and static-file updates'
"$VENV_DIR/bin/python" manage.py migrate --noinput
"$VENV_DIR/bin/python" manage.py collectstatic --noinput
"$VENV_DIR/bin/python" manage.py check

remote_step 'Restarting the application'
/bin/bash -lc "$RESTART_CMD"

remote_step "Deployment complete: $(git rev-parse --short HEAD)"
REMOTE_SCRIPT

step "Deployment complete: $RELEASE_REV"
