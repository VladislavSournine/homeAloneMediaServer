#!/bin/bash
set -e

echo "=== homeAloneMediaServer — Docker Install ==="

# 1. Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker not found. Install from https://docs.docker.com/get-docker/"
    exit 1
fi

# 2. Check Docker Compose (v2 preferred, v1 fallback)
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "ERROR: Docker Compose not found."
    exit 1
fi

# 3. Clone or use current directory
INSTALL_DIR="${1:-$HOME/homeAloneMediaServer}"
if [ ! -f "$INSTALL_DIR/server.py" ]; then
    echo "Cloning into $INSTALL_DIR..."
    git clone https://github.com/VladislavSournine/homeAloneMediaServer "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# 4. .env setup
cp .env.example .env
printf "Path to your media folder (e.g. /mnt/usb/Movies): "
read -r MEDIA_INPUT
if [ -z "$MEDIA_INPUT" ]; then
    echo "ERROR: MEDIA_PATH cannot be empty."
    exit 1
fi
# Use python3 for portable in-place edit (avoids sed -i portability issues)
python3 -c "
import re, sys
content = open('.env').read()
content = re.sub(r'MEDIA_PATH=.*', 'MEDIA_PATH=' + sys.argv[1], content)
open('.env', 'w').write(content)
" "$MEDIA_INPUT"

# 5. Create data dir, add to .gitignore
mkdir -p ./data
touch .gitignore
grep -qxF 'data/' .gitignore || echo 'data/' >> .gitignore
grep -qxF '.env' .gitignore || echo '.env' >> .gitignore

# 6. Config setup
cp config.example.json ./data/config.json

# 7. Optional auth token
printf "Auth token (leave empty to disable — set one if exposing to internet): "
read -r AUTH_INPUT
if [ -n "$AUTH_INPUT" ]; then
    python3 -c "
import json, sys
cfg = json.load(open('./data/config.json'))
cfg['auth_token'] = sys.argv[1]
json.dump(cfg, open('./data/config.json', 'w'), indent=2)
" "$AUTH_INPUT"
fi

# 8. Start
$COMPOSE up -d

IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
PORT=$(python3 -c "import json; print(json.load(open('./data/config.json')).get('port', 8765))")

echo ""
echo "=== Server started ==="
echo "URL: http://$IP:$PORT"
echo ""
echo "Next steps:"
echo "  - Edit ./data/config.json to add tmdb_api_key (optional, for movie metadata)"
echo "  - Run ./update_docker.sh to update to the latest version"
echo "  - See docs/remote-access.md for internet access setup"
