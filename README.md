# LTM Node Control (demo)

Concept demo: check a list of IPs against (mock) F5 LTM nodes, see which are in LTM and their
enabled/disabled status, and disable/enable them in bulk. No real LTM is contacted.

- `frontend/` Vue 3 + Quasar (Vite). Currently runs on mock data (`src/mock.js`).
- `backend/` Flask skeleton (`/api/health`); DB + endpoints come next.

## Run
```
cd frontend && npm install && npm run dev      # http://localhost:5173
cd backend  && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python app.py   # :5000
```
