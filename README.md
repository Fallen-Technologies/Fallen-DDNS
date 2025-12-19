# Fallen DDNS

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Cloudflare](https://img.shields.io/badge/Cloudflare-F38020?style=for-the-badge&logo=Cloudflare&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Fallen DDNS is an automated dynamic DNS service that monitors your public IP address and keeps your Cloudflare DNS records synchronized. When your IP changes, it automatically updates all matching A records across every zone in your Cloudflare account, no manual intervention required.

Perfect for home labs, self-hosted services, or any environment where your public IP may change and you need DNS records to stay current across multiple domains.

## Features

- **Automatic IP Monitoring** - Checks your public IP every 5 minutes with randomized jitter
- **Multi-Zone Support** - Updates DNS records across all Cloudflare zones with a single API key
- **PostgreSQL Integration** - Persistent IP storage for reliable change detection
- **Docker Ready** - Fully containerized with Docker Compose support
- **Detailed Logging** - Track every IP change and DNS update
- **Smart Updates** - Only updates records that actually match your old IP

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Cloudflare API token with `Zone:Read` and `DNS:Edit` permissions

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
   - **Permissions**: Zone → DNS → Edit
   - **Zone Resources**: Include → All Zones
   - **Client IP Address Filtering**: Leave blank
   - **TTL**: Leave blank
6. Click **Continue to Summary**
7. Copy the token and use it as `CF_API_KEY`

## How It Works

1. **IP Check** - Every 5 minutes (±60 seconds jitter), the service retrieves your current public IP
2. **Comparison** - Compares the current IP with the stored IP in PostgreSQL
3. **Zone Scan** - If changed, fetches all zones from your Cloudflare account
4. **Record Update** - Identifies and updates all A records pointing to the old IP
5. **Database Update** - Stores the new IP for future comparisons

## Support

Need help? Submit a ticket on our community Discord:

[![Discord](https://img.shields.io/badge/Discord-%237289DA.svg?logo=discord&logoColor=white)](https://discord.fallenservers.com)
