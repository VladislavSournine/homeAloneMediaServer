#!/usr/bin/env python3
"""
Mac HTTP proxy for Keenetic opkg and pip installs.
Forwards requests to mirrors.bfsu.edu.cn (for opkg) and pypi.org (for pip).
Usage: python3 entware_proxy.py [--port 8080]
"""
import http.server
import urllib.request
import argparse

OPKG_MIRROR = "https://mirrors.bfsu.edu.cn/entware"

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[proxy] {fmt % args}")

    def do_GET(self):
        path = self.path.lstrip("/")
        # Route opkg requests to Entware mirror
        if path.startswith("mipselsf-k3.4"):
            target = f"{OPKG_MIRROR}/{path}"
        else:
            target = f"https://{path}"
        try:
            req = urllib.request.Request(target, headers={"User-Agent": "opkg/entware"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_error(502, str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    print(f"Entware proxy listening on port {args.port}")
    http.server.HTTPServer(("", args.port), ProxyHandler).serve_forever()
