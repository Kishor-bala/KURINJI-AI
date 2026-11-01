"""
Root FastAPI entrypoint for Vercel deployment.
Exposes the Kurinji FastAPI application instance from backend.app.main.
Includes a diagnostic startup guard to surface any import or runtime exceptions.
"""
import sys

try:
    from backend.app.main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    err_trace = traceback.format_exc()
    print(f"[FATAL STARTUP ERROR] {err_trace}", file=sys.stderr)
    app = FastAPI(title="Kurinji Startup Error Diagnostic")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def startup_error_fallback(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "FastAPI failed to start during module import",
                "path_requested": path,
                "traceback": err_trace.splitlines(),
            },
        )

__all__ = ["app"]
