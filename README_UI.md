Marvel Champions - React UI

This project ships a minimal React frontend (no build) under `static/ui` served by Flask.

Quick run (system prerequisites):
- Python 3.11+ recommended
- If you run into `distutils`/`eventlet` import errors, install system packages: `sudo apt install python3-distutils` on Debian/Ubuntu

Install & run (venv recommended):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

Notes:
- The server uses a MongoDB collection `lobbies` for persistent lobby state if a MongoDB is available (see `config.py`). If Mongo is not available the app will still run but lobbies will fail to persist.
- The frontend caches fetched decks and modules in localStorage.
- Socket.IO is used for real-time lobby updates; the client loads Socket.IO from CDN.
