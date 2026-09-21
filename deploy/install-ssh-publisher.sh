#!/usr/bin/env bash
# Run once as root, after approving the repository's dedicated deployment key.
set -euo pipefail
[[ $EUID == 0 && $# == 1 ]] || { echo 'Usage: sudo bash deploy/install-ssh-publisher.sh PUBLIC_KEY_FILE' >&2; exit 1; }
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
key_file="$1"
python3 - "$key_file" <<'PY'
from pathlib import Path
import re
import sys
key = Path(sys.argv[1]).read_text().strip()
if not re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/]+={0,2}(?: [^\r\n]+)?', key):
    raise SystemExit('Expected one plain Ed25519 public key, without authorized_keys options')
PY
ssh-keygen -lf "$key_file" >/dev/null
[[ "$(getent passwd wojiecihuo | cut -d: -f6)" == /opt/wojiecihuo ]] || exit 1
[[ "$(id -u wojiecihuo)" != 0 ]] || exit 1
[[ "$(passwd -S wojiecihuo | awk '{print $2}')" == L ]] || { echo 'Deployment account must already have a locked password' >&2; exit 1; }

library=/usr/local/lib/wojiecihuo-publisher
config=/etc/ssh/wojiecihuo-publisher.conf
authorized=/etc/ssh/authorized_keys/wojiecihuo
backup="$(mktemp -d /etc/ssh/wojiecihuo-backup.XXXXXX)"
cp -p /etc/ssh/sshd_config "$backup/sshd_config"
[[ ! -e "$config" ]] || cp -p "$config" "$backup/publisher.conf"
[[ ! -e "$authorized" ]] || cp -p "$authorized" "$backup/authorized_keys"
old_shell="$(getent passwd wojiecihuo | cut -d: -f7)"
restore() {
  cp -p "$backup/sshd_config" /etc/ssh/sshd_config
  if [[ -e "$backup/publisher.conf" ]]; then cp -p "$backup/publisher.conf" "$config"; else rm -f "$config"; fi
  if [[ -e "$backup/authorized_keys" ]]; then cp -p "$backup/authorized_keys" "$authorized"; else rm -f "$authorized"; fi
  usermod --shell "$old_shell" wojiecihuo
  /usr/sbin/sshd -t && systemctl reload ssh
  echo "Publisher setup failed; restored SSH settings from $backup" >&2
}
trap restore ERR

install -d -m 755 -o root -g root "$library" /etc/ssh/authorized_keys
install -m 644 -o root -g root "$source_dir/ssh_gateway.py" "$library/ssh_gateway.py"
install -m 644 -o root -g root "$source_dir/release.py" "$library/release.py"
printf 'restrict %s\n' "$(cat "$key_file")" > "$authorized"
chmod 644 "$authorized"
chown root:root "$authorized"
cat > "$config" <<'EOF'
Match User wojiecihuo
    AuthenticationMethods publickey
    PubkeyAuthentication yes
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    AuthorizedKeysFile /etc/ssh/authorized_keys/wojiecihuo
    ForceCommand /usr/bin/python3 -I /usr/local/lib/wojiecihuo-publisher/ssh_gateway.py
    DisableForwarding yes
    PermitTTY no
    PermitUserRC no
EOF
chmod 644 "$config"
chown root:root "$config"
# Append outside sshd_config.d: Match sections must follow the global settings.
if ! grep -qxF "Include $config" /etc/ssh/sshd_config; then
  printf '\n# Dedicated blog publisher\nInclude %s\n' "$config" >> /etc/ssh/sshd_config
fi
/usr/sbin/sshd -t
/usr/sbin/sshd -T -C user=wojiecihuo,host=localhost,addr=127.0.0.1 > "$backup/effective-config"
for expected in \
  'authenticationmethods publickey' \
  'passwordauthentication no' \
  'kbdinteractiveauthentication no' \
  'authorizedkeysfile /etc/ssh/authorized_keys/wojiecihuo' \
  'forcecommand /usr/bin/python3 -I /usr/local/lib/wojiecihuo-publisher/ssh_gateway.py' \
  'disableforwarding yes' 'permittty no' 'permituserrc no'; do
  grep -qxF "$expected" "$backup/effective-config"
done
usermod --shell /bin/sh wojiecihuo
systemctl reload ssh
trap - ERR
printf 'Restricted publisher installed. Previous SSH settings: %s\n' "$backup"
