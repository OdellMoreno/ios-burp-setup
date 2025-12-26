#!/usr/bin/env python3
"""Generate and host an iOS Wi-Fi proxy profile for Burp Suite testing."""

import argparse
import http.server
import os
import socket
import uuid
from pathlib import Path
import plistlib

import qrcode

PROXY_PORT = 8082
SERVER_PORT = 8000
PROFILE_FILENAME = "burp-wifi-proxy.mobileconfig"


def get_local_ip() -> str:
    """Detect the local LAN IP address by opening a UDP socket."""
    ip_address = "127.0.0.1"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip_address = sock.getsockname()[0]
    except OSError:
        pass
    return ip_address


def _sanitize_identifier(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in ("-", ".")).strip(".")


def build_profile(ssid: str, proxy_ip: str) -> bytes:
    """Create the Apple Configuration Profile payload in plist XML format."""
    profile_uuid = str(uuid.uuid4())
    wifi_uuid = str(uuid.uuid4())

    sanitized_ssid = _sanitize_identifier(ssid) or "wifi"
    payload = {
        "PayloadContent": [
            {
                "AutoJoin": True,
                "EncryptionType": "Any",
                "HIDDEN_NETWORK": False,
                "PayloadDescription": "Configures Wi-Fi proxy settings",
                "PayloadDisplayName": f"{ssid} Wi-Fi",
                "PayloadIdentifier": f"com.example.wifi.{sanitized_ssid}",
                "PayloadType": "com.apple.wifi.managed",
                "PayloadUUID": wifi_uuid,
                "PayloadVersion": 1,
                "ProxyType": "Manual",
                "ProxyServer": proxy_ip,
                "ProxyServerPort": PROXY_PORT,
                "SSID_STR": ssid,
            }
        ],
        "PayloadDescription": "Installs Wi-Fi proxy settings for Burp Suite",
        "PayloadDisplayName": "Burp Suite Wi-Fi Proxy",
        "PayloadIdentifier": f"com.example.burp-proxy.{sanitized_ssid}",
        "PayloadOrganization": "Burp Proxy Setup",
        "PayloadType": "Configuration",
        "PayloadUUID": profile_uuid,
        "PayloadVersion": 1,
    }

    return plistlib.dumps(payload, fmt=plistlib.FMT_XML)


def write_profile(profile_data: bytes, output_path: Path) -> None:
    output_path.write_bytes(profile_data)


def print_qr(url: str) -> None:
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


class ProfileHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, profile_path: Path, **kwargs):
        self.profile_path = profile_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path in {"/", ""}:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                """
                <!doctype html>
                <html lang=\"en\">
                  <head>
                    <meta charset=\"utf-8\">
                    <title>Burp Suite Wi-Fi Proxy</title>
                    <style>
                      body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; padding: 3rem; }
                      a.button { background: #0070f3; color: #fff; padding: 0.75rem 1.5rem; border-radius: 8px; text-decoration: none; }
                    </style>
                  </head>
                  <body>
                    <h1>Install Wi-Fi Proxy Profile</h1>
                    <p>Tap the button below on your iOS device to install the profile.</p>
                    <p><a class=\"button\" href=\"/download\">Download</a></p>
                  </body>
                </html>
                """.encode("utf-8")
            )
            return

        if self.path == "/download":
            if not self.profile_path.exists():
                self.send_error(404, "Profile not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/x-apple-aspen-config")
            self.send_header(
                "Content-Disposition",
                f"attachment; filename={self.profile_path.name}",
            )
            self.end_headers()
            self.wfile.write(self.profile_path.read_bytes())
            return

        self.send_error(404, "Not found")

    def handle_one_request(self) -> None:
        try:
            super().handle_one_request()
        except ConnectionResetError:
            return


def run_server(profile_path: Path) -> None:
    handler = lambda *args, **kwargs: ProfileHandler(
        *args, profile_path=profile_path, **kwargs
    )
    with http.server.ThreadingHTTPServer(("0.0.0.0", SERVER_PORT), handler) as httpd:
        httpd.daemon_threads = True
        httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate and host an iOS Wi-Fi proxy profile for Burp Suite."
    )
    parser.add_argument("ssid", help="Wi-Fi SSID to configure")
    args = parser.parse_args()

    ip_address = get_local_ip()
    profile_data = build_profile(args.ssid, ip_address)
    profile_path = Path.cwd() / PROFILE_FILENAME
    write_profile(profile_data, profile_path)

    url = f"http://{ip_address}:{SERVER_PORT}/"
    print(f"Profile written to {profile_path}")
    print(f"Serving profile at {url}")
    print("Scan this QR code on your iOS device:")
    print_qr(url)

    try:
        run_server(profile_path)
    except KeyboardInterrupt:
        print("\nShutting down server.")


if __name__ == "__main__":
    main()
