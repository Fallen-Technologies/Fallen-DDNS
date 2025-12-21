# Fallen DDNS

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Cloudflare](https://img.shields.io/badge/Cloudflare-F38020?style=for-the-badge&logo=Cloudflare&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Fallen DDNS is an automated dynamic DNS service that monitors your public IP address and keeps your Cloudflare DNS records synchronized. When your IP changes, it automatically updates all matching A records across every zone in your Cloudflare account, no manual intervention required.

Perfect for home labs, self-hosted services, or any environment where your public IP may change and you need DNS records to stay current across multiple domains.

## Features

- **Automatic IP Monitoring** - Checks your public IP every 5 minutes with randomized jitter
- **Multi-Zone Support** - Updates DNS records across all Cloudflare zones with a single API key
- **Firewall Access Rule Management** - Automatically updates Cloudflare firewall access rules when your IP changes
- **PostgreSQL Integration** - Persistent IP storage for reliable change detection
- **Docker Ready** - Fully containerized with Docker Compose support
- **Detailed Logging** - Track every IP change, DNS update, and firewall rule modification
- **Smart Updates** - Only updates records and rules that actually match your old IP

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Cloudflare API token with the following permissions:
  - `Zone:Read` - To list all zones in your account
  - `DNS:Edit` - To update DNS records
  - `Account Firewall Access Rules:Write` - To update firewall access rules

### Docker Compose

Create a `compose.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: fallen-ddns-db
    environment:
      POSTGRES_DB: fallen_ddns
      POSTGRES_USER: ddns_user
      POSTGRES_PASSWORD: your_secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ddns-network
    restart: unless-stopped

  fallen-ddns:
    image: ghcr.io/fallen-technologies/fallen-ddns:latest
    container_name: fallen-ddns
    environment:
      # Database Configuration
      DB_HOST: postgres
      DB_PORT: 5432
      DB_USER: ddns_user
      DB_PASS: your_secure_password_here
      DB_NAME: fallen_ddns
      
      # Cloudflare Configuration
      CF_API_KEY: your_cloudflare_api_token_here
    depends_on:
      - postgres
    networks:
      - ddns-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  ddns-network:
    driver: bridge
```

## Getting a Cloudflare API Token

1. In Cloudflare, go to **Profile** (top right corner)
2. Select **API Tokens**
3. Click **Create Token**
4. Select **Create Custom Token**
5. Set permissions:
   - **Permissions**: 
     - Zone → DNS → Edit
     - Account → Account Firewall Access Rules → Edit
   - **Zone Resources**: Include → All Zones
   - **Account Resources**: Include → All Accounts
   - **Client IP Address Filtering**: Leave blank
   - **TTL**: Leave blank
6. Click **Continue to Summary**
7. Copy the token and use it as `CF_API_KEY`

## Setting Up Firewall Access Rules

To enable automatic firewall rule updates, you need to create an initial IP access rule in Cloudflare:

1. In Cloudflare, select any domain you own
2. Go to **Security** → **WAF** → **Tools**
3. Under **IP Access Rules**, add a new entry:
   - **IP**: Your current public IP address
   - **Action**: Allow
   - **Zone**: All websites in account
   - **Note**: Add a description (e.g., "Home network access")
4. Click **Add**

This creates an account-level firewall rule that whitelists your IP address across all domains in your Cloudflare account. When your IP changes, Fallen DDNS will automatically delete this rule and recreate it with your new IP address, ensuring uninterrupted access to your protected sites.

## How It Works

1. **IP Check** - Every 5 minutes (±60 seconds jitter), the service retrieves your current public IP
2. **Comparison** - Compares the current IP with the stored IP in PostgreSQL
3. **Zone Scan** - If changed, fetches all zones from your Cloudflare account
4. **DNS Record Update** - Identifies and updates all A records pointing to the old IP
5. **Firewall Rule Update** - Updates all firewall access rules that reference the old IP
6. **Database Update** - Stores the new IP for future comparisons

## Support

Need help? Submit a ticket on our community Discord:

[![Discord](https://img.shields.io/badge/Discord-%237289DA.svg?logo=discord&logoColor=white)](https://discord.fallenservers.com)
