# TravManager — Project Structure & Setup Guide
# ===============================================
# This document describes how to set up and run the project.

## Directory Structure

```
travmanager/
├── README.md                          # This file
├── docker-compose.yml                 # Local development stack
├── .env.example                       # Environment variables template
│
├── backend/
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Backend container
│   ├── alembic.ini                    # DB migration config
│   ├── migrations/
│   │   └── 001_initial_schema.sql     # ✅ Complete PostgreSQL schema
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI application entry point
│       ├── config.py                  # Settings & environment
│       │
│       ├── api/                       # API routes
│       │   ├── __init__.py
│       │   ├── auth.py                # Login, register, sessions
│       │   ├── stable.py              # Stable management
│       │   ├── horses.py              # Horse CRUD, training, feeding
│       │   ├── races.py               # Race entries, results, tactics
│       │   ├── drivers.py             # Driver contracts, booking
│       │   ├── transfer.py            # Auction, scouting, claiming
│       │   ├── breeding.py            # Breeding, stallion registry
│       │   ├── finances.py            # Transactions, sponsors
│       │   ├── events.py              # News feed, daily events
│       │   ├── v75.py                 # V75 tipping meta-game
│       │   └── admin.py               # Game state, NPC management
│       │
│       ├── core/                      # Shared utilities
│       │   ├── __init__.py
│       │   ├── database.py            # SQLAlchemy/asyncpg setup
│       │   ├── auth.py                # JWT, password hashing
│       │   ├── deps.py                # FastAPI dependencies
│       │   └── scheduler.py           # Celery Beat / APScheduler
│       │
│       ├── models/                    # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── stable.py
│       │   ├── horse.py
│       │   ├── driver.py
│       │   ├── race.py
│       │   ├── transfer.py
│       │   ├── breeding.py
│       │   ├── finance.py
│       │   └── event.py
│       │
│       ├── services/                  # Business logic
│       │   ├── __init__.py
│       │   ├── stable_service.py      # Stable operations
│       │   ├── horse_service.py       # Training, feeding, health
│       │   ├── race_service.py        # Race scheduling, entry, results
│       │   ├── driver_service.py      # Contract, compatibility calc
│       │   ├── transfer_service.py    # Auctions, scouting
│       │   ├── breeding_service.py    # Genetics, nick effects
│       │   ├── finance_service.py     # Economy, sponsors
│       │   ├── npc_service.py         # NPC stable/horse generation
│       │   ├── event_service.py       # Daily events, morning report
│       │   ├── achievement_service.py # Achievement tracking
│       │   └── scheduler_service.py   # Cron jobs (races, daily updates)
│       │
│       └── engine/                    # Race simulation
│           ├── __init__.py
│           └── race_engine.py         # ✅ Complete simulation engine
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   │
│   └── src/
│       ├── app/                       # Next.js App Router
│       │   ├── layout.tsx             # Root layout
│       │   ├── page.tsx               # Landing page
│       │   ├── (auth)/
│       │   │   ├── login/page.tsx
│       │   │   └── register/page.tsx
│       │   ├── (game)/
│       │   │   ├── layout.tsx         # Game layout (sidebar, topbar)
│       │   │   ├── dashboard/page.tsx # Main dashboard / "Kontor"
│       │   │   ├── stable/page.tsx    # Horse list
│       │   │   ├── stable/[id]/page.tsx # Horse detail
│       │   │   ├── races/page.tsx     # Race schedule
│       │   │   ├── races/[id]/page.tsx # Race detail + live viewer
│       │   │   ├── transfer/page.tsx  # Transfer market
│       │   │   ├── breeding/page.tsx  # Breeding center
│       │   │   ├── drivers/page.tsx   # Driver management
│       │   │   ├── v75/page.tsx       # V75 tipping
│       │   │   ├── finances/page.tsx  # Economy overview
│       │   │   └── settings/page.tsx  # Stable settings
│       │   └── api/                   # Next.js API routes (proxy)
│       │
│       ├── components/
│       │   ├── ui/                    # Generic UI (Button, Card, etc.)
│       │   ├── game/                  # Game-specific components
│       │   │   ├── HorseCard.tsx
│       │   │   ├── StatBar.tsx
│       │   │   ├── RaceViewer.tsx     # Live race animation
│       │   │   ├── TacticsSelector.tsx
│       │   │   ├── ShoeSelector.tsx
│       │   │   ├── FeedPlanEditor.tsx
│       │   │   ├── CompatibilityBadge.tsx
│       │   │   ├── AuctionCard.tsx
│       │   │   ├── PedigreeTree.tsx
│       │   │   └── MorningReport.tsx
│       │   └── layout/
│       │       ├── Sidebar.tsx
│       │       ├── TopBar.tsx
│       │       └── GameLayout.tsx
│       │
│       ├── hooks/
│       │   ├── useStable.ts
│       │   ├── useHorse.ts
│       │   ├── useRace.ts
│       │   ├── useWebSocket.ts        # Live race connection
│       │   └── useApi.ts
│       │
│       └── lib/
│           ├── api.ts                 # API client
│           ├── types.ts               # TypeScript interfaces
│           ├── constants.ts           # Game constants
│           └── utils.ts               # Helpers
│
└── docs/
    ├── TravManager_GameDesign.md          # ✅ Game design document v1
    ├── TravManager_RaceEngine_Spec.md     # ✅ Race engine spec
    ├── TravManager_Complete_Spec_v2.md    # ✅ Full mechanics spec
    ├── API_ENDPOINTS.md                   # ✅ All API endpoints
    └── ARCHITECTURE.md                    # This file
```

## Key Technical Decisions

### Backend: Python + FastAPI
- **Why**: Python is ideal for the race simulation math, FastAPI is fast and modern
- **ORM**: SQLAlchemy 2.0 with async support (asyncpg)
- **Background jobs**: Celery with Redis broker (race simulation, daily updates)
- **WebSocket**: Socket.IO for live race viewing

### Frontend: Next.js + TypeScript + Tailwind
- **Why**: SSR for SEO (landing pages), App Router for clean structure
- **Styling**: Tailwind CSS (dark theme, gold accents)
- **State**: React Query (TanStack Query) for server state
- **Real-time**: Socket.IO client for live race feed

### Database: PostgreSQL
- **Why**: Complex relational data (horses, races, genetics, finances)
- **All monetary values stored in öre** (1 kr = 100 öre) to avoid float issues
- **JSONB** for flexible data (race snapshots, sector times, scouting reports)

### Cache/Queue: Redis
- **Sessions**: JWT refresh tokens
- **Leaderboards**: Sorted sets for division standings
- **Job queue**: Celery broker for background tasks
- **Pub/sub**: Live race event broadcasting
