#!/bin/sh
set -e

if [ ! -f /data/config.json ]; then
    echo "[homeAloneMediaServer] /data/config.json not found, copying from config.example.json"
    cp /app/config.example.json /data/config.json
fi

auth=$(python3 -c "import json; print(json.load(open('/data/config.json')).get('auth_token', ''))")
if [ -z "$auth" ]; then
    echo "[homeAloneMediaServer] WARNING: auth_token is empty — server has no authentication"
fi

exec python3 server.py --config /data/config.json
