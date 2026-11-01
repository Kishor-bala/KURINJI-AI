import sys
import json
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add possible root directories to sys.path so 'backend' package is always found
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

for p in [current_dir, parent_dir, Path("/var/task"), Path("/var/task/backend")]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from backend.app.main import app
            from mangum import Mangum
            # Run health query directly
            from backend.app.database.connection import get_db_connection
            vocab_count = 0
            try:
                with get_db_connection() as conn:
                    vocab_count = conn.execute("SELECT COUNT(*) FROM vocabulary;").fetchone()[0]
            except Exception as dbe:
                vocab_count = f"DB warning: {dbe}"

            response_data = {
                "status": "healthy",
                "python_version": sys.version,
                "vocabulary_count": vocab_count,
                "sys_path": sys.path[:5],
            }
            status_code = 200
        except Exception as e:
            response_data = {
                "status": "import_error",
                "python_version": sys.version,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            status_code = 500

        body = json.dumps(response_data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
