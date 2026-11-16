import ipaddress
import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request
from flask_cors import CORS

DB_PATH = Path(os.environ.get("DB_PATH") or Path(__file__).with_name("ltm.db"))

# Fake LTM nodes (ip, name, partition). Every 6th one starts disabled.
SEED_NODES = [
    ("10.10.1.11", "web-node-01", "Prod"), ("10.10.1.12", "web-node-02", "Prod"),
    ("10.10.1.13", "web-node-03", "Prod"), ("10.10.1.14", "web-node-04", "Prod"),
    ("10.10.2.21", "app-node-01", "Prod"), ("10.10.2.22", "app-node-02", "Prod"),
    ("10.10.2.23", "app-node-03", "Prod"), ("10.10.2.24", "app-node-04", "Prod"),
    ("10.10.3.31", "api-node-01", "Prod"), ("10.10.3.32", "api-node-02", "Prod"),
    ("10.10.3.33", "api-node-03", "Prod"), ("10.10.3.34", "api-node-04", "Prod"),
    ("10.20.1.41", "db-proxy-01", "Common"), ("10.20.1.42", "db-proxy-02", "Common"),
    ("10.20.1.43", "cache-node-01", "Common"), ("10.20.1.44", "cache-node-02", "Common"),
    ("10.20.2.51", "auth-node-01", "Common"), ("10.20.2.52", "auth-node-02", "Common"),
    ("10.20.2.53", "pay-node-01", "Common"), ("10.20.2.54", "pay-node-02", "Common"),
    ("10.30.1.61", "uat-web-01", "UAT"), ("10.30.1.62", "uat-web-02", "UAT"),
    ("10.30.1.63", "uat-app-01", "UAT"), ("10.30.1.64", "uat-app-02", "UAT"),
]

app = Flask(__name__)
CORS(app)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """CREATE TABLE IF NOT EXISTS ltm_node (
               ip TEXT PRIMARY KEY,
               name TEXT NOT NULL,
               partition TEXT NOT NULL,
               status TEXT NOT NULL CHECK (status IN ('enabled', 'disabled'))
           )"""
    )
    if not db.execute("SELECT 1 FROM ltm_node LIMIT 1").fetchone():
        db.executemany(
            "INSERT INTO ltm_node VALUES (?, ?, ?, ?)",
            [(ip, name, part, "disabled" if i % 6 == 5 else "enabled")
             for i, (ip, name, part) in enumerate(SEED_NODES)],
        )
        db.commit()
    db.close()


def parse_ips(text):
    """Split on whitespace/comma/semicolon, drop duplicates, keep order."""
    return list(dict.fromkeys(t for t in re.split(r"[\s,;]+", text or "") if t))


def is_ipv4(s):
    try:
        ipaddress.IPv4Address(s)
        return True
    except ValueError:
        return False


@app.get("/api/health")
def health():
    return jsonify(ok=True)


@app.post("/api/check")
def check():
    ips = parse_ips((request.get_json(silent=True) or {}).get("text"))
    db = get_db()
    rows = []
    for ip in ips:
        node = db.execute("SELECT * FROM ltm_node WHERE ip = ?", (ip,)).fetchone()
        if node:
            rows.append({**dict(node), "in_ltm": True})
        else:
            rows.append({"ip": ip, "in_ltm": False, "valid": is_ipv4(ip)})
    return jsonify(rows=rows)


def set_status(status):
    ips = (request.get_json(silent=True) or {}).get("ips") or []
    db = get_db()
    updated = 0
    for ip in ips:
        updated += db.execute(
            "UPDATE ltm_node SET status = ? WHERE ip = ?", (status, ip)
        ).rowcount
    db.commit()
    return jsonify(updated=updated, status=status)


@app.post("/api/disable")
def disable():
    return set_status("disabled")


@app.post("/api/enable")
def enable():
    return set_status("enabled")


init_db()

if __name__ == "__main__":
    # Bound to localhost: the Vite dev server (and nginx) proxy /api to it.
    app.run(host="127.0.0.1", port=5000, debug=True)
