# ios-burp-setup

A Python tool that auto-generates Apple Configuration Profiles (.mobileconfig) to force Wi-Fi proxy settings on iOS devices. Streamlines the setup process for mobile application penetration testing with Burp Suite.

## Usage

```bash
python3 ios_burp_setup.py "Your Wi-Fi SSID"
```

1. Connect your iOS device to the specified Wi-Fi network.
2. Scan the QR code printed in the terminal or open the URL on the same network.
3. Tap **Download** to install the profile in iOS Settings.
4. Trust the profile when prompted.

## Notes

- The script hosts the profile on port `8000` and configures the proxy to `8082`.
- If your laptop firewall blocks inbound connections, temporarily disable it or allow incoming connections so your iOS device can reach the download page and proxy server.
- Optional: add a convenience alias for launching Burp with the config file:
  ```bash
  alias burp='java -jar /opt/burp/burpsuite_community.jar --config-file=""'
  ```
