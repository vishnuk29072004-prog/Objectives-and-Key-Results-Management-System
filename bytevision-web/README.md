# byteVision Web

Production React frontend for the Task Bot / byteVision OKR FastAPI backend.

## Stack

- React 19 + Vite
- Material UI
- Axios, React Router, Framer Motion, Recharts, Day.js, React Hook Form, Notistack

## Setup

```bash
cd bytevision-web
npm install
npm run dev
```

Opens on **http://localhost:3001** (Axios calls FastAPI on `:8000` directly; Vite also proxies `/api`).

## Backend

Ensure the FastAPI server is running:

```bash
cd ../backend
python api_server_agentic.py
```

## Notes

- All OKR data is fetched from live REST APIs — no mock data.
- Settings / Profile preferences are client-side only (backend has no settings/profile endpoints).
- Analytics heatmap & productivity scores are **derived** from dashboard/objectives responses.
