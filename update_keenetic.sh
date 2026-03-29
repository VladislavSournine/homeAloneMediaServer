#!/bin/bash
set -e

HOST=""
SSH_PORT=222
REMOTE_DIR="/opt/homeplayer"
# Server-side files only — entware_proxy.py and serve_proxy.sh are Mac-only tools
SERVER_FILES="server.py scanner.py metadata.py watch_history.py subtitles.py config.py"

while [ $# -gt 0 ]; do
    case "$1" in
        --host) HOST="$2"; shift 2 ;;
        --port) SSH_PORT="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [ -z "$HOST" ]; then
    printf "Router IP (e.g. 192.168.1.1): "
    read -r HOST
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Transferring files to $HOST (SSH port $SSH_PORT)..."
for f in $SERVER_FILES; do
    echo "  -> $f"
    ssh -o PubkeyAuthentication=no -p "$SSH_PORT" root@"$HOST" "cat > $REMOTE_DIR/$f" < "$f"
done

echo "Restarting service..."
ssh -o PubkeyAuthentication=no -p "$SSH_PORT" root@"$HOST" \
    "/opt/etc/init.d/S99homeplayer restart"

echo "Done. To rotate auth_token: edit /opt/homeplayer/config.json on the router, then restart."
