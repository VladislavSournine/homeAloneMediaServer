#!/bin/sh
# Install homeplayer-server on Keenetic via Entware
# Usage: sh install_keenetic.sh --proxy 192.168.1.140
# Run on the router via SSH (port 222)

set -e

PROXY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --proxy) PROXY="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [ -z "$PROXY" ]; then
  echo "Usage: sh install_keenetic.sh --proxy <mac-ip>"
  exit 1
fi

echo "==> Configuring opkg to use proxy $PROXY:8080"
printf 'src/gz entware http://%s:8080/mipselsf-k3.4\nsrc/gz keendev http://%s:8080/mipselsf-k3.4/keenetic\ndest root /\nlists_dir ext /opt/var/opkg-lists\narch all 100\narch mipsel-3.4 150\narch mipsel-3.4_kn 200\n' "$PROXY" "$PROXY" > /opt/etc/opkg.conf

echo "==> Installing Python3 via opkg"
opkg update
opkg install python3 python3-pip

echo "==> Installing requests via pip"
pip install --proxy "http://$PROXY:8080" requests

echo "==> Copying server files"
mkdir -p /opt/homeplayer /opt/homeplayer/data
for f in server.py scanner.py metadata.py watch_history.py subtitles.py config.py; do
  cp "/opt/share/homeplayer-server/$f" /opt/homeplayer/
done

echo "==> Creating config.json"
printf 'Auth token for remote access (leave empty to disable): '
read AUTH_TOKEN
python3 -c "
import json, sys
cfg = {
  'media_path': '/opt/share/Movies',
  'port': 8765,
  'tmdb_api_key': '',
  'data_dir': '/opt/homeplayer/data',
  'scan_interval_seconds': 300,
  'auth_token': sys.argv[1]
}
json.dump(cfg, open('/opt/homeplayer/config.json', 'w'), indent=2)
" "$AUTH_TOKEN"

echo "==> Creating autostart script"
printf '#!/bin/sh\ncase "$1" in\n  start)\n    python3 /opt/homeplayer/server.py --config /opt/homeplayer/config.json >> /opt/var/log/homeplayer.log 2>&1 &\n    echo $! > /opt/var/run/homeplayer.pid\n    ;;\n  stop)\n    kill $(cat /opt/var/run/homeplayer.pid 2>/dev/null) 2>/dev/null || true\n    ;;\n  restart)\n    $0 stop; sleep 1; $0 start\n    ;;\nesac\n' > /opt/etc/init.d/S99homeplayer
chmod +x /opt/etc/init.d/S99homeplayer

echo "==> Done!"
echo "Edit /opt/homeplayer/config.json, then: /opt/etc/init.d/S99homeplayer start"
