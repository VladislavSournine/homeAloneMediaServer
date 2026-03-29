# homeAloneMediaServer

Lightweight media server for local MP4/subtitle libraries. Works with [homeAlonePlayer](https://github.com/VladislavSournine/homeAlonePlayer) (Android/Fire TV). Runs on Keenetic routers or any Linux/Raspberry Pi machine.

## Features

- Serves local MP4 files with range-seeking support
- Subtitle (.vtt) lookup and serving
- Movie/series metadata from TMDb (optional)
- Watch history (position + duration per entry)
- Optional bearer token auth for remote access
- Background library scanner (mtime-based, no full rescans)

## Requirements

- Python 3.8+ **or** Docker + Docker Compose
- `requests` pip package (TMDb only; not needed if `tmdb_api_key` is empty)

## Choose your install path

### Option A: Keenetic router (Entware)

See [docs/keenetic.md](docs/keenetic.md) for the full guide.

Quick start (requires Mac running `./serve_proxy.sh` on same network):

```bash
scp -P 222 install_keenetic.sh root@192.168.1.1:/tmp/
ssh root@192.168.1.1 -p 222
sh /tmp/install_keenetic.sh --proxy 192.168.1.140  # replace with your Mac's IP
```

### Option B: Linux / Raspberry Pi / Mac (Docker)

```bash
git clone https://github.com/VladislavSournine/homeAloneMediaServer
cd homeAloneMediaServer
./install_docker.sh
```

## Configuration

Edit `config.json` (Keenetic: `/opt/homeplayer/config.json`, Docker: `./data/config.json`):

| Field | Default / Required | Description |
|---|---|---|
| `media_path` | *(required)* | Absolute path to media folder |
| `data_dir` | *(required)* | Absolute path for persistent data |
| `port` | `8765` | HTTP port |
| `tmdb_api_key` | `""` | TMDb API key (leave empty to disable) |
| `scan_interval_seconds` | `300` | How often to scan for new files |
| `auth_token` | `""` | Bearer token for auth (leave empty for LAN use) |

## File Naming Convention

```
Movies/
├── Movie Title/
│   ├── Movie Title_1080p.mp4
│   ├── Movie Title_1080p_Українська.vtt   ← preferred subtitle
│   └── poster.jpg                          ← optional local poster
Series/
├── Series Title/
│   ├── Series Title_S01E01_720p.mp4
│   └── Series Title_S01E01_720p_Українська.vtt
```

Supported quality tags: `360p`, `480p`, `720p`, `1080p`, `1080p Ultra`, `2160p`, `4k`.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/library` | Full library JSON |
| GET | `/stream/{path}` | Range-aware MP4 stream (.mp4 only) |
| GET | `/poster/{title}` | Local poster or TMDb redirect (`{title}` = folder name) |
| GET | `/subtitles/{path}` | .vtt subtitle file (path relative to media folder, without extension) |
| GET | `/metadata/{tmdb_id}` | Cached TMDb metadata |
| GET | `/watch_history` | All watch history |
| POST | `/watch_history` | Save watch position |
| DELETE | `/watch_history/{id}` | Remove entry |

When `auth_token` is set, all requests require: `Authorization: Bearer <token>`

## Remote Access

See [docs/remote-access.md](docs/remote-access.md) for setup guides:
- KeenDNS (Keenetic built-in DDNS)
- DuckDNS (any router)
- WireGuard VPN (no auth needed)

## Updating

**Docker:**
```bash
./update_docker.sh
```

**Keenetic:**
```bash
./update_keenetic.sh --host 192.168.1.1
```
