# Keenetic Install Guide

## Prerequisites

- Keenetic router with Entware installed (USB disk, ext4 formatted, OPKG component enabled in Keenetic UI)
- Mac on the same network (needed as opkg/pip proxy — Keenetic cannot download packages directly)
- SSH access to router (default: `ssh root@192.168.1.1 -p 222`)

> If Entware is not yet installed, follow [Keenetic's official guide](https://help.keenetic.com/hc/en-us/articles/360021214160) before continuing.

## Step 1: Start Mac proxy

On your Mac, open a terminal and keep it running:

```bash
cd homeAloneMediaServer
./serve_proxy.sh
```

This starts a local HTTP proxy on port 8080 that forwards opkg and pip requests.

## Step 2: Copy install script to router

```bash
scp -P 222 install_keenetic.sh root@192.168.1.1:/tmp/
```

## Step 3: Run install on router

```bash
ssh root@192.168.1.1 -p 222
sh /tmp/install_keenetic.sh --proxy 192.168.1.140
```

Replace `192.168.1.140` with your Mac's IP address.

The script will:
1. Configure opkg to use your Mac as proxy
2. Install python3 and pip via opkg
3. Install the `requests` package via pip
4. Copy server files to `/opt/homeplayer/`
5. Prompt for optional auth token
6. Create `/opt/homeplayer/config.json`
7. Create `/opt/etc/init.d/S99homeplayer` autostart script

## Step 4: Configure

Edit config on the router:

```bash
ssh -p 222 root@192.168.1.1
vi /opt/homeplayer/config.json
```

Minimum config:
```json
{
  "media_path": "/opt/share/Movies",
  "port": 8765,
  "tmdb_api_key": "",
  "data_dir": "/opt/homeplayer/data",
  "scan_interval_seconds": 300,
  "auth_token": ""
}
```

Set `media_path` to wherever your USB media is mounted (check with `ls /opt/share/` or `ls /media/`).

> **Important:** The installer creates `config.json` with placeholder values. You must set `media_path` to your actual media folder before the server will serve any files.

## Service Management

```bash
# Start
/opt/etc/init.d/S99homeplayer start

# Stop
/opt/etc/init.d/S99homeplayer stop

# Restart
/opt/etc/init.d/S99homeplayer restart

# Check if running
ps | grep server.py
```

## Viewing Logs

The service writes stdout/stderr to `/opt/var/log/homeplayer.log`:

```bash
tail -f /opt/var/log/homeplayer.log
```

To see output interactively:
```bash
/opt/etc/init.d/S99homeplayer stop
cd /opt/homeplayer && python3 server.py --config config.json
```

## Updating

From your Mac (in the homeAloneMediaServer directory):

```bash
./update_keenetic.sh --host 192.168.1.1
```

This transfers only server Python files and restarts the service. Does not touch `config.json`.

## Troubleshooting

**opkg update fails with 403:**
Mac proxy is not running. Start `./serve_proxy.sh` and retry.

**`ModuleNotFoundError: No module named 'requests'`:**
pip install failed. Run manually:
```bash
ssh -p 222 root@192.168.1.1
pip install --proxy http://192.168.1.140:8080 requests
```

**Server starts but library is empty:**
Check `media_path` in config — must be absolute and exist. Check USB is mounted.

**Port 8765 already in use:**
Another process using the port. Check with `ss -tlnp | grep 8765` and kill it, or change `port` in config.

## Rotating auth_token

```bash
ssh -p 222 root@192.168.1.1
vi /opt/homeplayer/config.json
# Edit "auth_token" field
/opt/etc/init.d/S99homeplayer restart
```

Update homeAlonePlayer's Setup screen with the new token.
