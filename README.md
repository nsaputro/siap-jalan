# SiapJalan

[![CI](https://github.com/nsaputro/siap-jalan/actions/workflows/ci.yml/badge.svg)](https://github.com/nsaputro/siap-jalan/actions/workflows/ci.yml)

SiapJalan ("Ready to Go" in Indonesian) is a smart travel packing assistant that helps you build the perfect packing list for any trip. Pick your activities — Hiking, Beach, Flight, Business — and SiapJalan merges the relevant templates into one deduplicated list, then optionally refines it with AI suggestions based on your destination and weather forecast.

---

![Screenshot placeholder](docs/screenshot.png)

---

## Features

- **Activity-based templates** — 16 built-in activities (Flight, Beach, Hiking, Camping, Skiing, Business, City Break, Road Trip, Cycling, Running, Diving, Surfing, Photography, Backpacking, Family/Kids, Swimming). Combine multiple activities; duplicates are merged automatically.
- **AI packing suggestions** — powered by the Anthropic Claude API. Generates destination-aware suggestions (e.g. cold-weather extras for Hokkaido in January).
- **Weather integration** — fetches a live forecast from Open-Meteo (no API key required) to inform packing recommendations.
- **Template propagation** — editing a shared activity template pushes the change to all active trips using that template.
- **Home Assistant addon** — native HA ingress support, persistent `/data/` storage, multi-arch (amd64 + aarch64).
- **Standalone deployment** — Docker Compose stack with a React + Vite frontend and a FastAPI backend.

---

## Installation

### Home Assistant Addon

1. In HA go to **Settings → Add-ons → Add-on Store**.
2. Click the three-dot menu (⋮) → **Repositories** and add:
   ```
   https://github.com/nsaputro/siap-jalan
   ```
3. Find **SiapJalan** in the store and click **Install**.
4. In the addon **Configuration** tab, paste your `anthropic_api_key` (optional — AI suggestions are disabled without it).

### Docker Compose (standalone)

1. Clone the repo and create your env file:
   ```bash
   git clone https://github.com/nsaputro/siap-jalan.git
   cd siap-jalan
   cp backend/.env.example backend/.env
   # Edit backend/.env and set ANTHROPIC_API_KEY
   ```
2. Start the stack:
   ```bash
   docker compose up --build
   ```
3. Open **http://localhost:5173** in your browser. The API docs are at **http://localhost:8000/docs**.

---

## Development

See [CLAUDE.md](CLAUDE.md) for full development instructions including:

- Backend (FastAPI + SQLAlchemy) setup
- Frontend (React 19 + TypeScript + Vite) setup
- Linting commands
- Architecture overview (standalone vs HA addon)
- Git / PR / versioning policy
- CI/CD and release workflow
