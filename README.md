# ✂️ Sunrise Salon — AI Voice Agent

A real-time AI voice receptionist for **Sunrise Salon, Indiranagar, Bengaluru**. Callers can speak naturally to book or cancel appointments, check stylist availability, ask about services and pricing, or get answers to common questions — all via voice in the browser.

> ⏳ **Please Note — Render Free Tier Sleep & Wake-up Time:**  
> The backend server and voice worker are hosted on Render's free tier. If the service has been inactive for 15 minutes, Render puts the server into sleep mode. When you launch the web app or click **Start Call** for the first time, **it may take 50 to 90 seconds to spin up and connect**. Please be patient! Once it is awake, voice interactions and responses will be fast and seamless.

> 📋 **Salon Owner Handover Guide:**  
> Looking for a non-technical guide for salon staff and owners? Check out the [Salon Owner Handover Guide](HANDOVER_GUIDE.md) or download the printable PDF version: [Sunrise_Salon_Voice_Assistant_Handover_Guide.pdf](Sunrise_Salon_Voice_Assistant_Handover_Guide.pdf).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (React)                     │
│        LiveKit Client SDK  ↔  FastAPI /token endpoint    │
└─────────────────────┬───────────────────────────────────┘
                      │  WebRTC audio (via LiveKit Cloud)
┌─────────────────────▼───────────────────────────────────┐
│              LiveKit Agents Worker (Python)              │
│  STT: Deepgram Nova-3 · LLM: GPT-4.1-mini · TTS: Cartesia Sonic-3  │
│                 Function tools → PostgreSQL              │
└─────────────────────────────────────────────────────────┘
```

- The **FastAPI** server issues LiveKit JWT tokens to the browser.
- **LiveKit Cloud** relays WebRTC audio between the browser and the agent worker.
- The **agent worker** runs the STT → LLM → TTS pipeline and calls database tools to manage appointments.
- **PostgreSQL** (Render Postgres / Neon / Supabase) stores appointments, stylists, services, and FAQs. The database auto-seeds on first boot.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🎙️ Real-time voice call | WebRTC via LiveKit Cloud; audio streams directly in the browser |
| 🤖 AI receptionist | GPT-4.1-mini with IST-aware calendar rules and Indian-English handling |
| 📅 Appointment booking | Collects name, service, stylist, and time; prevents double-booking with row-level locks |
| ❌ Appointment cancellation | Cancel by customer name + stylist + slot |
| 🔍 Availability check | Per-stylist, per-slot or full-day view |
| 💇 Service & pricing lookup | 7 services across 3 stylists |
| ❓ FAQ | Payment, parking, walk-ins, cancellation policy |
| 🛡️ Validation | Past-date guard, working-day check, working-hour check, 30-min slot alignment |
| 🌐 Deployable | One-click `render.yaml` for Render.com |

---

## 🗂️ Project Structure

```
Sunrise_voice_agent/
├── render.yaml                  # Render.com deployment config
├── backend/
│   ├── Procfile                 # honcho: web (FastAPI) + worker (agent)
│   ├── pyproject.toml           # Python deps (uv)
│   ├── .env.example             # Required environment variables
│   └── src/
│       ├── agent.py             # LiveKit agent: tools + SalonAssistant
│       ├── app.py               # FastAPI: /token endpoint + CORS
│       ├── controllers.py       # DB query logic (availability, booking, FAQ...)
│       ├── database.py          # SQLAlchemy models + auto-seed
│       └── config.py            # Pydantic settings
└── frontend/
    ├── package.json             # React + LiveKit client deps (Bun/npm)
    ├── vite.config.js
    ├── .env.example
    └── src/
        ├── App.jsx              # UI: call button, mic toggle, audio visualizer
        └── App.css              # Styles
```

---

## 🧰 Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Runtime | Python 3.13 |
| Package manager | [uv](https://github.com/astral-sh/uv) |
| Web framework | FastAPI + Uvicorn |
| Voice agent | [LiveKit Agents](https://docs.livekit.io/agents/) ~1.3 |
| STT | Deepgram Nova-3 (`en`) |
| LLM | OpenAI GPT-4.1-mini |
| TTS | Cartesia Sonic-3 |
| VAD | Silero (via `livekit-agents[silero]`) |
| Database | PostgreSQL (async via SQLAlchemy + asyncpg) |
| Process manager | [Honcho](https://honcho.readthedocs.io/) |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 19 |
| Bundler | Vite 8 |
| Styling | Tailwind CSS 4 |
| Voice SDK | LiveKit Client 2 |
| Package manager | Bun (or npm) |

---

## ⚙️ Environment Variables

### Backend — `backend/.env`

Copy `backend/.env.example` and fill in your credentials:

```env
# LiveKit Cloud project
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# PostgreSQL — Render Postgres, Neon, or Supabase
# postgres:// and postgresql:// are both handled automatically
DATABASE_URL=postgresql://user:password@hostname:5432/dbname

# AI model API keys
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
CARTESIA_API_KEY=your_cartesia_api_key
GROQ_API_KEY=your_groq_api_key   # optional / future use
```

### Frontend — `frontend/.env`

```env
VITE_BACKEND_URL=http://localhost:8000
```

> **Note:** For production, set `VITE_BACKEND_URL` to your deployed backend URL (e.g. `https://sunrise-salon-backend.onrender.com`).

---

## 🚀 Running Locally

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (`pip install uv` or `curl -Ls https://astral.sh/uv/install.sh | sh`)
- [Bun](https://bun.sh/) (or Node.js 18+)
- A PostgreSQL database (local or cloud)
- LiveKit Cloud project credentials
- Deepgram, OpenAI, and Cartesia API keys

### 1. Clone & configure

```bash
git clone <repo-url>
cd Sunrise_voice_agent

# Backend env
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# Frontend env
cp frontend/.env.example frontend/.env
# Set VITE_BACKEND_URL=http://localhost:8000
```

### 2. Backend

```bash
cd backend
uv sync              # install dependencies into .venv
uv run honcho start  # starts both FastAPI (web) and agent worker
```

The two processes started by Honcho:
- **web** → `uvicorn src.app:app` on `$PORT` (defaults to 5000 via honcho)
- **worker** → `python src/agent.py start` — connects to LiveKit Cloud and waits for jobs

> The database tables are created and seeded automatically on the first request to the agent.

### 3. Frontend

```bash
cd frontend
bun install      # or: npm install
bun run dev      # or: npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📞 Using the Voice Agent

1. Open the frontend in your browser.
2. Click **Start Call** — the browser requests a LiveKit token from the backend and joins the room.
   > ⏳ *If connecting to the live Render deployment after an inactive period, the backend may take 50–90 seconds to wake up from sleep mode. Please keep the window open and wait for the status to change to "On call — speak now!".*
3. The agent greets you: *"Hello! Welcome to Sunrise Salon. How can I help you with your appointment today?"*
4. Speak naturally. Example prompts:
   - *"I'd like to book a haircut with Anita on Friday at 11 AM."*
   - *"Is Rahul Shetty available on Thursday evening?"*
   - *"How much does a facial cost?"*
   - *"What are your payment options?"*
   - *"Cancel my appointment with Kavya Nair at 10 AM tomorrow."*
5. Click **End Call** to disconnect.

---

## 🗄️ Database Schema

The database is **auto-created and seeded on first boot** — no migration scripts needed.

### `stylists`

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment |
| name | String | Full name (e.g. `Anita Rao`) |
| specialties | String | e.g. `Haircuts and styling` |
| working_days | String | Comma-separated abbreviations e.g. `Mon,Tue,Wed,Thu,Fri,Sat` |
| start_time | String | `HH:MM` e.g. `10:00` |
| end_time | String | `HH:MM` e.g. `14:00` |

### `services`

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment |
| service_name | String | e.g. `Haircut (women)` |
| stylist_name | String | Linked stylist name |
| price | String | e.g. `Rs 600` |

### `faqs`

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment |
| category | String | e.g. `Payment`, `Policies`, `Walk-ins & Parking` |
| content | Text | Full FAQ answer |

### `appointments`

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment |
| customer_name | String | Caller's full name |
| service | String | Service booked |
| stylist | String | Stylist's canonical name |
| slot_time | DateTime | Naive IST datetime |
| status | String | `Confirmed` |

> **Double-booking prevention:** A `UNIQUE` constraint on `(stylist, slot_time)` backed by a row-level `SELECT … FOR UPDATE` lock prevents race conditions.

---

## 🌐 Deploying to Render

The repo includes a [`render.yaml`](render.yaml) for one-click deployment.

1. Push the repo to GitHub.
2. In [Render Dashboard](https://dashboard.render.com/) → **New → Blueprint** → connect your repo.
3. Render will create a **web service** (`sunrise-salon-backend`) running both the FastAPI server and the agent worker via Honcho.
4. Add the following **environment variables** in the Render service settings:

| Variable | Description |
|---|---|
| `LIVEKIT_URL` | Your LiveKit Cloud WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `DATABASE_URL` | PostgreSQL connection string |
| `OPENAI_API_KEY` | OpenAI API key |
| `DEEPGRAM_API_KEY` | Deepgram API key |
| `CARTESIA_API_KEY` | Cartesia API key |

5. For the **frontend**, deploy separately (Vercel / Netlify / Render Static Site) and set `VITE_BACKEND_URL` to the backend's public URL before building.

---

## 👨‍💼 Salon Data (Pre-seeded)

### Stylists

| Name | Specialties | Working Days | Hours (IST) |
|---|---|---|---|
| Anita Rao | Haircuts & styling | Mon – Sat | 10:00 – 14:00 |
| Rahul Shetty | Hair colour & spa | Tue, Thu, Sat | 16:00 – 20:00 |
| Kavya Nair | Facials & clean-ups | Mon, Wed, Fri | 09:00 – 13:00 |

### Services & Pricing

| Service | Stylist | Price |
|---|---|---|
| Haircut (women) | Anita Rao | Rs 600 |
| Haircut (men) | Anita Rao | Rs 400 |
| Blow dry & styling | Anita Rao | Rs 500 |
| Hair colour | Rahul Shetty | From Rs 2,500 |
| Hair spa | Rahul Shetty | Rs 1,200 |
| Facial | Kavya Nair | Rs 1,500 |
| Clean-up | Kavya Nair | Rs 800 |

### Policies

- **Slots:** 30 minutes each (10:00, 10:30, 11:00, …)
- **Closed:** Sundays
- **Cancellations:** Free up to 2 hours before the appointment
- **Late arrivals:** More than 15 minutes late → booking may be moved to the next free slot
- **Walk-ins:** Welcome; booked customers are served first
- **Payments:** Cash, UPI, Cards
- **Parking:** Street parking only
- **Address:** 12 Lake Road, Indiranagar, Bengaluru

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

*Built with ❤️ using LiveKit Agents, FastAPI, and React.*
