# Task Bot — Full Stack OKR Assistant

React frontend + FastAPI backend with LangGraph/LangChain agents and SQLite.

## Structure

- `frontend/` — React.js UI
- `backend/` — FastAPI API, LangGraph agents, reminder scheduler
- `okr.db` — SQLite database (also present under `backend/`)

## Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for Google Gemini and/or OpenRouter (optional for LLM features)

## Setup

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your keys
python api_server_agentic.py
```

API: http://localhost:8000

### Frontend

```powershell
cd frontend
npm install
npm start
```

App: http://localhost:3000

## Notes

- Do not commit `.env`, `venv/`, or `node_modules/`
- Reminder emails require SMTP settings in `.env`
