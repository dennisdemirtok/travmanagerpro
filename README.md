# 🏇 TravManager

**Online harness racing manager game** — Hattrick meets Swedish trotting.

Build and manage your stable, train horses, hire drivers, race in real-time simulated races, breed champions, and climb the divisions.

## Quick Start

```bash
# 1. Clone and setup
cp .env.example .env

# 2. Start everything
docker-compose up -d

# 3. Access
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API docs:  http://localhost:8000/docs
# Test race: http://localhost:8000/api/v1/test-race
```

## Project Structure

```
travmanager/
├── backend/          Python FastAPI + Race Engine
│   ├── app/
│   │   ├── engine/   Race simulation (deterministic, step-based)
│   │   ├── api/      REST endpoints
│   │   ├── services/ Business logic
│   │   └── models/   SQLAlchemy ORM
│   └── migrations/   PostgreSQL schema
├── frontend/         Next.js + TypeScript + Tailwind
└── docs/             Game design & API specs
```

## Key Documents

| Document | Description |
|----------|-------------|
| `docs/ARCHITECTURE.md` | Tech stack, directory structure, decisions |
| `docs/API_ENDPOINTS.md` | All API endpoints with request/response |
| `docs/TravManager_GameDesign.md` | Game concept & vision |
| `docs/TravManager_Complete_Spec_v2.md` | All game mechanics in detail |
| `docs/TravManager_RaceEngine_Spec.md` | Race simulation deep-dive |

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Celery
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Infra**: Docker, Hetzner Cloud (production)

## Game Time Model

1 real week = 2 game weeks. Races run every day. A horse can race ~2x per real week with good recovery management. The game always has something to do: daily checkups, training, feeding, scouting, press releases, transfers.

## Race Engine

The core simulation (`backend/app/engine/race_engine.py`) is:
- **Deterministic** — seeded RNG, same input = same output
- **Step-based** — 100m steps, full physics per step
- **Transparent** — detailed post-race analysis with sector times
- Factors: speed, endurance, mentality, start, sprint, balance, strength, shoes, weather, surface, tactics, driver skill, compatibility, gallop risk, energy management
