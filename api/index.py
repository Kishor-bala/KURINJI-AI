import sys
import traceback
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add possible root directories to sys.path so 'backend' package is always found
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

for p in [current_dir, parent_dir, Path("/var/task"), Path("/var/task/backend")]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from backend.app.main import app
except Exception as e:
    tb = traceback.format_exc()
    app = FastAPI()

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def debug_fallback(path_name: str):
        task_files = []
        if Path("/var/task").is_dir():
            task_files = [str(x.relative_to(Path("/var/task"))) for x in Path("/var/task").rglob("*")][:50]
        return JSONResponse(
            status_code=500,
            content={
                "error": "FastAPI initialization failed on Vercel",
                "exception": str(e),
                "traceback": tb,
                "sys_path": sys.path,
                "task_files": task_files,
            },
        )
