# FluentBridge AI

Local-first AI English tutor for Persian-speaking learners preparing for academic English and TOEFL. Built with **Django + Django REST Framework** (backend) and **React + Vite** (frontend).

**React is the main UI.** Django serves `/api/`, `/admin/`, and redirects `/` to the frontend — use **http://localhost:5173** for learning, not port 8000.

## Features

- **Two-stage learning journey** — Stage 1: B2 / TOEFL 80+ readiness; Stage 2: Academic / TOEFL 100+ readiness with lesson progression and readiness checks
- **Dashboard & daily plan** — Today's focus, targeted practice, and stage-aware study tasks
- **Grammar lessons** — Structured topics with AI coach chat
- **Reading Coach** — Generate original passages, analyze your own text, or try TOEFL-style reading simulation
- **Listening Coach** — Transcript analysis and quiz practice
- **Writing Coach** — Editing, paraphrasing, revision feedback, and essay practice
- **Speaking Coach** — Audio attempts with rubric-style feedback
- **Shadowing** — Pronunciation and rhythm practice
- **Vocabulary** — SRS flashcards, seed library, and category decks
- **Mistake Clinic** — Mistakes grouped by pattern with review routes
- **Provider-agnostic AI** — Switch between Ollama, OpenAI, and Anthropic via prompt templates in Django admin

## Tech stack

| Layer | Stack |
|-------|--------|
| Backend | Django 6, DRF, SQLite (dev) |
| Frontend | React 19, Vite, React Router |
| AI | Ollama (local), OpenAI, Anthropic |
| Auth | Django session + CSRF |

## Quick start

### 1. Backend

```bash
cd ~/Projects/english-learning
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set API keys / Ollama host
python manage.py migrate
python manage.py createsuperuser
```

### 2. Frontend

```bash
cd frontend && npm install && cd ..
npm install   # root dev runner (concurrently)
```

### 3. Ollama (optional, for local AI)

This project defaults to Ollama on port **11435** (so it can coexist with other apps on 11434):

```bash
OLLAMA_HOST=http://127.0.0.1:11435 ollama serve
ollama pull qwen2.5:7b
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 4. Run

```bash
source venv/bin/activate
npm run dev        # or: make dev
```

| Service | URL |
|---------|-----|
| **App (React)** | http://localhost:5173 |
| Django admin | http://127.0.0.1:8000/admin/ |
| API health | http://127.0.0.1:8000/api/health/ |

Log in with the Django user you created. Protected routes redirect to `/login` when unauthenticated.

## Environment variables

Copy `.env.example` to `.env`. Important settings:

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Secret key (required for production) |
| `DJANGO_DEBUG` | `true` in development |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `OLLAMA_HOST` | Ollama base URL (default `http://127.0.0.1:11435`) |
| `DEFAULT_OLLAMA_MODEL` | Main tutor model (default `qwen2.5:7b`) |
| `OPENAI_API_KEY` | OpenAI (also used for Whisper/TTS when configured) |
| `ANTHROPIC_API_KEY` | Anthropic |
| `FRONTEND_URL` | React URL for redirects and CORS |

After changing Ollama model names in the DB or env:

```bash
python manage.py fix_ollama_model_names
```

Check Ollama: `GET /api/ollama/status/`

## Development commands

From the project root (with `venv` activated):

```bash
make dev              # Django + React together
make backend          # Django only (port 8000)
make frontend         # Vite only (port 5173)
make check            # Django system check
make test             # Backend tests (tutor app)
make frontend-lint    # Oxlint
make frontend-build   # Production frontend build
make build            # Alias for frontend-build
make clean-mac        # Remove .DS_Store / AppleDouble files
make clean-pycache    # Remove __pycache__ and *.pyc
make hard-backup      # Shareable tarball (excludes .env, .git, venv, node_modules)
make hard-backup-private  # Full tarball including .env and .git
```

Equivalent npm scripts: `npm run dev`, `npm run check`, `npm run build`, `npm run dev:all` (Ollama + Django + React).

## App routes (frontend)

| Path | Page |
|------|------|
| `/dashboard` | Learning overview, today's focus, journey progress |
| `/readiness` | Stage readiness check |
| `/lesson` | Grammar lessons by stage |
| `/plan` | Daily study plan |
| `/reading` | Reading Coach |
| `/listening` | Listening Coach |
| `/writing` | Writing Coach |
| `/speaking` | Speaking Coach |
| `/shadowing` | Shadowing practice |
| `/vocab` | Vocabulary review and decks |
| `/mistakes` | Mistake Clinic |
| `/profile` | Profile and settings |

## API overview

All learning endpoints require login. React calls Django `/api/` only — never AI providers directly.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/auth/me/` | Current user |
| `POST /api/auth/login/` | Session login |
| `GET /api/dashboard/` | Dashboard + coach focus |
| `GET /api/readiness/` | Readiness report |
| `GET /api/plan/today/` | Today's plan |
| `POST /api/plan/today/generate/` | Generate plan |
| `POST /api/reading/generate/` | Generate reading practice |
| `POST /api/reading/submit/` | Submit reading answers |
| `POST /api/reading/analyze/` | Analyze a pasted passage |
| `GET /api/mistakes/` | Saved mistakes |
| `GET /api/vocab/due/` | Due vocabulary |
| `POST /api/chat/` | Grammar / writing / speaking chat |
| `POST /api/speaking/attempt-audio/` | Speaking feedback |
| `GET /api/prompts/` | Active AI prompt templates |

Full URL map: `tutor/urls.py`.

## Vocabulary seeds

Starter deck and import commands:

```bash
python manage.py load_starter_vocab
python manage.py import_vocab_seed --file data/vocab/starter_500.csv
python manage.py enrich_vocab_seed --category toefl_academic --limit 20
```

Seeds use `approved=False` until reviewed in Django admin. Only approved seeds appear for regular users in Explore / Category Decks.

## Local network (phone / tablet)

1. Find your LAN IP: `ipconfig getifaddr en0`
2. Add to `.env`:

```env
FRONTEND_URL=http://YOUR_IP:5173
FRONTEND_ORIGIN=http://YOUR_IP:5173
ALLOWED_HOSTS=YOUR_IP
EXTRA_CORS_ORIGINS=http://YOUR_IP:5173
```

3. Run `make dev` and open **http://YOUR_IP:5173** on the device.

Use Chrome or Edge for microphone features (Speaking / Shadowing).

## Project structure

```
english-learning/
├── core/                   # Django project settings
├── tutor/                  # Main app
│   ├── ai/                 # Provider-agnostic AI clients
│   ├── prompts/            # Default prompt templates
│   ├── reading_practice.py # Reading generation & scoring
│   ├── learning_journey.py # Two-stage curriculum & readiness
│   ├── dashboard_coach.py  # Dashboard focus logic
│   ├── plan.py             # Daily study plan
│   └── management/commands/
├── frontend/               # React + Vite UI
├── data/                   # Vocabulary seed CSVs
├── Makefile
├── requirements.txt
└── manage.py
```

## Verify

```bash
make check
make test
make frontend-lint
make frontend-build
```

## Backup

```bash
make hard-backup          # Shareable (no .env, no .git)
make hard-backup-private  # Includes secrets and git history
```

Archives are written to the parent directory, e.g. `../english-learning-share-YYYYMMDD-HHMMSS.tar.gz`.

## License & content

Reading and TOEFL-style materials generated by the app are **original practice content**, not official ETS/TOEFL passages. Verify licenses before bulk-importing external vocabulary or text datasets.
