# Fallen DDNS

Fallen DDNS is an internal dynamic DNS service. It checks the office's public IP every minute, compares it with the stored value in our Postgres DB, and updates any CloudFlare A records using the old IP to the new IP.

## How It Works

- Retrieves the public IP every minute.
- Compares the current IP with the one in the database.
- If the IP has changed, finds and updates Cloudflare A records automatically.
