import sys
from pathlib import Path

# Add possible root directories to sys.path so 'backend' package is always found
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

for p in [current_dir, parent_dir, Path("/var/task")]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from backend.app.main import app
