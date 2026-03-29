# Remote Access Setup

By default homeAloneMediaServer is only accessible on your local network. This guide covers options for accessing it from a mobile phone over the internet.

> **Security:** When exposing the server to the internet, always set `auth_token` in `config.json`. See [Rotating auth_token](#rotating-auth_token) below.

---

## Option 1: KeenDNS (Keenetic routers)

**When to use:** You have a Keenetic router and want the simplest remote access setup.

Keenetic has a built-in DDNS service that gives you a `*.keenetic.pro` domain.

1. In Keenetic web UI: **Network Rules → Domain Name**
2. Enable KeenDNS, choose a name (e.g. `myhome.keenetic.pro`)
3. **Network Rules → Forwarding** → Add rule:
   - Protocol: TCP
   - External port: 8765
   - Internal IP: IP of the device running homeAloneMediaServer
   - Internal port: 8765
4. Set `auth_token` in `/opt/homeplayer/config.json` and restart
5. In homeAlonePlayer: enter `myhome.keenetic.pro:8765` as server address

---

## Option 2: DuckDNS (any router)

**When to use:** You don't have a Keenetic or want a portable DDNS solution that works with any router.

Free DDNS service at [duckdns.org](https://www.duckdns.org).

1. Register at duckdns.org → create a domain (e.g. `myhome.duckdns.org`)
2. Copy your token from the DuckDNS dashboard
3. Set up auto-update cron on the server machine:
   ```bash
   # Add to crontab (crontab -e):
   */5 * * * * curl -s "https://www.duckdns.org/update?domains=myhome&token=YOUR_TOKEN&ip=" > /tmp/duck.log
   ```
4. Forward port 8765 on your router to the server machine
5. Set `auth_token` in `config.json` and restart
6. In homeAlonePlayer: enter `myhome.duckdns.org:8765` as server address

---

## Option 3: WireGuard VPN — Keenetic (built-in WireGuard)

**When to use:** You want the most secure option and have a Keenetic router with built-in WireGuard support.

Traffic stays private — no need for `auth_token`.

1. In Keenetic web UI: **Internet → Other connections → WireGuard**
2. Click **+** to create a new WireGuard interface
3. Add a peer for your phone → Keenetic generates a QR code
4. On your phone: install [WireGuard](https://www.wireguard.com/install/) from Play Store / App Store
5. Scan the QR code → Connect
6. In homeAlonePlayer: use the router's WireGuard IP (e.g. `10.0.0.1:8765`)

---

## Option 4: WireGuard VPN — Linux / Raspberry Pi

**When to use:** You want the most secure option and your server runs on Linux or Raspberry Pi.

Traffic stays private — no need for `auth_token`.

```bash
# Install
sudo apt install wireguard

# Generate keys
wg genkey | tee server_private.key | wg pubkey > server_public.key
chmod 600 server_private.key
wg genkey | tee phone_private.key | wg pubkey > phone_public.key
chmod 600 phone_private.key

# /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server_private.key>

[Peer]
PublicKey = <phone_public.key>
AllowedIPs = 10.0.0.2/32

# Start
sudo wg-quick up wg0
# Allow WireGuard port through firewall (if ufw is enabled)
sudo ufw allow 51820/udp
sudo systemctl enable wg-quick@wg0
```

Phone config (import into WireGuard app):
```
[Interface]
PrivateKey = <phone_private.key>
Address = 10.0.0.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = <server_public.key>
# Find your public IP: curl ifconfig.me (use DuckDNS from Option 2 if your IP changes)
Endpoint = <your-public-ip>:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```

---

## Rotating auth_token

### Keenetic

```bash
ssh -p 222 root@192.168.1.1
vi /opt/homeplayer/config.json
# Change "auth_token" value, save, then:
/opt/etc/init.d/S99homeplayer restart
```

### Docker

```bash
# Edit ./data/config.json on the host machine
nano ./data/config.json
# Change "auth_token" value, save, then:
docker compose restart
```

---

## Comparison

| Option | Difficulty | Auth needed | Works on any router |
|---|---|---|---|
| KeenDNS | Easy | Yes | Keenetic only |
| DuckDNS | Medium | Yes | Yes |
| WireGuard (Keenetic) | Medium | No | Keenetic only |
| WireGuard (Linux/RPi) | Medium | No | Yes |
