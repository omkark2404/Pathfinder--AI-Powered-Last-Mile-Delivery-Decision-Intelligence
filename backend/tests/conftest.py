import os
import sys

# Ensure backend root is on sys.path when running bare `pytest`
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure tests default to SQLite fallback rather than connecting to external Postgres
os.environ.setdefault("DATABASE_URL", "")
