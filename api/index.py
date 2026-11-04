import os
import sys
from pathlib import Path

# Add project root directory to Python module search path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure serverless environment variables are configured
os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# Import the main FastAPI application instance
from backend.api.main import app

# Vercel entrypoint looks for 'app'
__all__ = ["app"]
