# Dark Angel Tracker

A self-hosted progressive web application for tracking personal health and habit metrics over time. Built with a Python Flask REST API backend, SQLite persistence, and a vanilla JS frontend — containerized with Docker and deployed behind an Nginx reverse proxy with SSL termination.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask, SQLite |
| Frontend | Vanilla HTML/CSS/JS |
| Container | Docker, Docker Compose |
| Reverse Proxy | Nginx Proxy Manager |
| Router | GL.iNet Flint 3 (BE9300) |
| Infrastructure | Proxmox VE, Ubuntu 22.04 LXC |

---

## Features

- REST API with full CRUD for daily log entries
- Tracks body composition metrics, sleep, nutrition, and daily habits
- Streak tracking and rolling averages
- Countdown timer with progress bar for goal-based milestones
- Delta indicators showing metric trends between entries
- Persistent SQLite storage surviving container restarts
- Responsive design, mobile-friendly
- Served over HTTPS via wildcard SSL certificate

---

## Architecture

```
Browser (local or remote via Tailscale)
  └── HTTPS request to progress.your-domain.com
        └── GL.iNet Flint 3 (router, bridge mode, 10.0.0.1)
              └── Nginx Proxy Manager (SSL termination, reverse proxy)
                    └── Flask app container (port 5000)
                          └── SQLite database (/data/tracker.db)

DNS Flow:
All devices → Flint 3 → AdGuard Home (10.0.0.137) → Cloudflare (1.1.1.1)
                                    └── Wildcard rewrite *.your-domain.com → NPM LXC
```

The app runs as a Docker container inside an LXC on Proxmox. The GL.iNet Flint 3 operates in bridge mode (Rogers XB10 modem passthrough), receiving a public IP directly from the ISP. Nginx Proxy Manager handles SSL termination using a wildcard certificate obtained via Cloudflare DNS challenge. Internal DNS resolution is handled by AdGuard Home with a wildcard rewrite pointing to the reverse proxy LXC. Remote access is handled by Tailscale with subnet routing advertising the full `10.0.0.0/24` network.

---

## Network Layout

| Host | IP | Role |
|------|----|------|
| Flint 3 | 10.0.0.1 | Router / DHCP / DNS forwarder |
| Proxmox | 10.0.0.234 | Hypervisor / Tailscale subnet router |
| NPM LXC | 10.0.0.136 | Reverse proxy, Docker host |
| AdGuard LXC | 10.0.0.137 | DNS, ad blocking |
| Jellyfin LXC | 10.0.0.134 | Media server |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/entries` | Retrieve all log entries |
| POST | `/api/entries` | Create or update an entry for a date |
| DELETE | `/api/entries/<id>` | Delete a specific entry |
| GET | `/api/stats` | Aggregated stats and latest metrics |

---

## Project Structure

```
dark-angel-tracker/
├── app.py                  # Flask application and API routes
├── Dockerfile              # Container build definition
├── requirements.txt        # Python dependencies
├── static/
│   └── index.html          # Single-page frontend
└── data/                   # SQLite database volume mount
    └── tracker.db
```

---

## Deployment

### Prerequisites

- Docker and Docker Compose installed on target host
- Nginx Proxy Manager running and accessible
- Wildcard SSL certificate configured in NPM
- AdGuard Home or other DNS server for internal resolution
- DNS wildcard rewrite pointing your subdomain to NPM host

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/TechAsura/dark-angel-tracker
cd dark-angel-tracker
```

**2. Add to your docker-compose.yml**

```yaml
services:
  dark-angel-tracker:
    build: ./dark-angel-tracker
    container_name: dark-angel-tracker
    restart: unless-stopped
    volumes:
      - ./dark-angel-tracker/data:/data
    ports:
      - "5000:5000"
```

**3. Build and start**

```bash
docker compose build dark-angel-tracker
docker compose up -d dark-angel-tracker
```

**4. Configure NPM proxy host**

- Domain: `progress.your-domain.com`
- Forward to: `YOUR_LXC_IP:5000`
- SSL: select your wildcard cert, force SSL enabled

**5. Access**

Navigate to `https://progress.your-domain.com`

---

## Updating the Frontend

Since static files are baked into the container image at build time, use `docker cp` for frontend-only updates without a full rebuild:

```bash
docker cp ./dark-angel-tracker/static/index.html dark-angel-tracker:/app/static/index.html
```

For backend changes, rebuild and restart:

```bash
docker compose build dark-angel-tracker
docker compose up -d dark-angel-tracker
```

---

## Data

All data is stored in a single SQLite file at `./dark-angel-tracker/data/tracker.db`. To back it up:

```bash
cp ./dark-angel-tracker/data/tracker.db ./dark-angel-tracker/data/tracker.db.bak
```

---

## Related

This project is part of a broader homelab infrastructure setup documented at [homelab-infrastructure](https://github.com/TechAsura/homelab-infrastructure).
