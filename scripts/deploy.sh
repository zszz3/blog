#!/usr/bin/env bash
set -euo pipefail
: "${ECS_HOST:?Set ECS_HOST}"
: "${ECS_USER:?Set ECS_USER}"
: "${ECS_SSH_KEY:?Set ECS_SSH_KEY}"
: "${ECS_KNOWN_HOSTS:?Set ECS_KNOWN_HOSTS}"
port="${ECS_PORT:-22}"
root="${ECS_SITE_ROOT:-/opt/wojiecihuo/site}"
[[ "$ECS_HOST" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ && "$ECS_USER" =~ ^[a-zA-Z_][a-zA-Z0-9_-]*$ && "$port" =~ ^[0-9]+$ && "$root" =~ ^/[a-zA-Z0-9/_-]+$ && "$root" != / ]] || { echo 'Invalid deployment settings'; exit 1; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
chmod 700 "$work"
printf '%s\n' "$ECS_SSH_KEY" > "$work/key"
printf '%s\n' "$ECS_KNOWN_HOSTS" > "$work/known_hosts"
chmod 600 "$work/key" "$work/known_hosts"
opts=(-i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o ConnectTimeout=15)
host="$ECS_USER@$ECS_HOST"
ssh "${opts[@]}" -p "$port" "$host" "mkdir -p '$root/incoming' '$root/tools'"
scp "${opts[@]}" -P "$port" deploy/release.py "$host:$root/tools/release.py"
if [[ "${DEPLOY_OPERATION:-publish}" == rollback ]]; then
  release="${ROLLBACK_RELEASE:-previous}"
  [[ "$release" == previous || "$release" =~ ^[0-9]+-[0-9]+-[a-f0-9]{40}$ ]] || exit 1
  ssh "${opts[@]}" -p "$port" "$host" "python3 '$root/tools/release.py' rollback --root '$root' --release '$release'"
else
  : "${GITHUB_SHA:?Set GITHUB_SHA}"
  : "${GITHUB_RUN_NUMBER:?Set GITHUB_RUN_NUMBER}"
  attempt="${GITHUB_RUN_ATTEMPT:-1}"
  [[ "$GITHUB_SHA" =~ ^[a-f0-9]{40}$ && "$GITHUB_RUN_NUMBER" =~ ^[0-9]+$ && "$attempt" =~ ^[0-9]+$ ]] || exit 1
  release="$GITHUB_RUN_NUMBER-$attempt-$GITHUB_SHA"
  COPYFILE_DISABLE=1 tar -czf "$work/site.tar.gz" -C dist .
  scp "${opts[@]}" -P "$port" "$work/site.tar.gz" "$host:$root/incoming/$release.tar.gz"
  ssh "${opts[@]}" -p "$port" "$host" "python3 '$root/tools/release.py' publish --root '$root' --archive '$root/incoming/$release.tar.gz' --release '$release' --run '$GITHUB_RUN_NUMBER'"
fi
