#!/usr/bin/env bash
set -euo pipefail
: "${ECS_HOST:?Set ECS_HOST}"
: "${ECS_USER:?Set ECS_USER}"
: "${ECS_SSH_KEY:?Set ECS_SSH_KEY}"
: "${ECS_KNOWN_HOSTS:?Set ECS_KNOWN_HOSTS}"
port="${ECS_PORT:-22}"
root="${ECS_SITE_ROOT:-/opt/wojiecihuo/site}"
[[ "$ECS_HOST" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ && "$ECS_USER" =~ ^[a-zA-Z_][a-zA-Z0-9_-]*$ && "$port" =~ ^[0-9]+$ && "$root" == /opt/wojiecihuo/site ]] || { echo 'Invalid deployment settings'; exit 1; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
chmod 700 "$work"
printf '%s\n' "$ECS_SSH_KEY" > "$work/key"
printf '%s\n' "$ECS_KNOWN_HOSTS" > "$work/known_hosts"
chmod 600 "$work/key" "$work/known_hosts"
opts=(-T -i "$work/key" -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$work/known_hosts" -o ConnectTimeout=15 -o ClearAllForwardings=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3)
host="$ECS_USER@$ECS_HOST"
if [[ "${DEPLOY_OPERATION:-publish}" == rollback ]]; then
  release="${ROLLBACK_RELEASE:-previous}"
  [[ "$release" == previous || "$release" =~ ^[0-9]+-[0-9]+-[a-f0-9]{40}$ ]] || exit 1
  ssh "${opts[@]}" -p "$port" "$host" "rollback $release"
elif [[ "${DEPLOY_OPERATION:-publish}" == publish ]]; then
  : "${GITHUB_SHA:?Set GITHUB_SHA}"
  : "${GITHUB_RUN_NUMBER:?Set GITHUB_RUN_NUMBER}"
  attempt="${GITHUB_RUN_ATTEMPT:-1}"
  [[ "$GITHUB_SHA" =~ ^[a-f0-9]{40}$ && "$GITHUB_RUN_NUMBER" =~ ^[0-9]+$ && "$attempt" =~ ^[0-9]+$ ]] || exit 1
  release="$GITHUB_RUN_NUMBER-$attempt-$GITHUB_SHA"
  COPYFILE_DISABLE=1 tar -czf "$work/site.tar.gz" -C dist .
  ssh "${opts[@]}" -p "$port" "$host" "publish $release" < "$work/site.tar.gz"
else
  echo 'Unsupported deployment operation' >&2
  exit 1
fi
