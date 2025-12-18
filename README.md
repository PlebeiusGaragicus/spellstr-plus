# spellstr-plus

A nostr-native spelling practice app for grade-school students. Users pay 1 sat per session via eCash (Cashu).

## Setup

### 1. Configure Environment

```bash
# Copy environment files
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# Edit as needed (defaults work for development)
nano frontend/.env
nano backend/.env
```

### 2. Environment Variables

**Frontend** (`frontend/.env`):
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

**Backend** (`backend/.env`):
| Variable | Description | Default |
|----------|-------------|---------|
| `MINT_URL` | Cashu mint URL for eCash redemption | `https://mint.minibits.cash/Bitcoin` |
| `WALLET_DB` | Path to wallet database (inside container) | `/app/wallet_db` |

### 3. Development

```bash
# Build and start with hot reload
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 4. Production

```bash
# Build and start production containers
docker-compose -f docker-compose.prod.yml up --build -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

- **Frontend:** http://localhost:3000 (nginx serving static build)
- **Backend API:** http://localhost:8000

---

## TODO

### Frontend (Svelte 5)
- [x] Project setup with Vite + Svelte 5
- [x] Top navbar with CypherTap login button (top right)
- [x] Landing page encouraging login/key creation
- [x] Practice session UI (listen, type, submit)
- [x] Text-to-speech integration (Web Speech API)
- [x] Celebration screen after 20 correct words
- [x] Stats tracking (correct/attempted)
- [x] Payment flow integration with backend

### Backend (Python FastAPI)
- [x] Project setup with FastAPI + uvicorn
- [x] Nutshell library integration for eCash redemption
- [x] `/api/redeem` endpoint - redeem user eCash token
- [x] `/api/session/start` endpoint - approve spelling session
- [x] `/api/words` endpoint - serve word list
- [x] CORS configuration for frontend

### Infrastructure
- [x] Docker Compose configuration
- [x] Frontend Dockerfile
- [x] Backend Dockerfile
- [x] Environment variable configuration (.env at project root)

### Remaining
- [ ] Production build configuration
- [ ] Nostr event signing for session verification
- [ ] Persistent session storage (Redis/SQLite)

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Svelte 5      │────▶│   FastAPI       │
│   Frontend      │     │   Backend       │
│   (port 5173)   │     │   (port 8000)   │
└─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │   Nutshell      │
                        │   (eCash)       │
                        └─────────────────┘
```

## User Flow

1. User lands on homepage, sees CypherTap button in navbar
2. User logs in / creates key via CypherTap
3. User pays 1 sat (eCash token sent to backend)
4. Backend redeems token via nutshell, approves session
5. User practices spelling (TTS reads word + sentence)
6. After 20 correct words, celebration screen appears