# LTM Node Control (demo)

Concept demo: check a list of IPs against (mock) F5 LTM nodes, see which are in LTM and their
enabled/disabled status, and disable/enable the selected nodes in bulk. No real LTM is contacted.

- `frontend/` Vue 3 + Vite, hand-written CSS. Built and served by nginx in its container.
- `backend/` Flask + SQLite (`ltm_node` table, seeded with 24 fake nodes), run by gunicorn.

## API
- `POST /api/check`   `{"text": "ip ip ..."}` -> each IP with `in_ltm`, name, partition, status
- `POST /api/disable` `{"ips": [...]}`
- `POST /api/enable`  `{"ips": [...]}`

## Run (containers)
```
docker compose up -d --build        # http://127.0.0.1:5445  (FRONTEND_PORT to change)
```
The frontend container proxies `/api` to the backend; the DB lives in the `ltm-data` volume.

## Run (dev)
```
cd frontend && npm install && npm run dev      # :5173, proxies /api to 127.0.0.1:5000
cd backend  && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python app.py
```
