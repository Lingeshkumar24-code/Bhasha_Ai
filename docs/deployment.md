# Deployment (Render)

## 1. Push this repo to GitHub
Do NOT commit `.env` files — only `.env.example`.

## 2. Create services on Render
Easiest: Render Dashboard → "New" → "Blueprint" → point at this repo. `render.yaml` defines
both services automatically. Or create manually:

**Backend (Web Service)**
- Root: repo root
- Build: `pip install -r backend/requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT --app-dir backend`
- Env vars: `GROQ_API_KEY`, `GROQ_MODEL`, `CORS_ORIGINS`

**Frontend (Static Site)**
- Build: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/dist`
- Env var: `VITE_API_BASE` = your backend's Render URL
- Add a rewrite rule `/* → /index.html` for client-side routing

## 3. Local development
```
# backend
cd backend
cp .env.example .env   # fill in GROQ_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload

# frontend (new terminal)
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 — Vite proxies /api and /health to the backend on :8000.
