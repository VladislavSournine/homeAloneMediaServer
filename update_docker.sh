#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "ERROR: Docker Compose not found."
    exit 1
fi

echo "Pulling latest changes..."
git pull

echo "Rebuilding and restarting..."
$COMPOSE up -d --build --remove-orphans

echo "Update complete."
