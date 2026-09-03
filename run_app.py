# run_app.py - Single-command runner for AI Research Gap Finder Full-Stack Application

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from backend.api.main import app
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print("\n=======================================================", flush=True)
    print(" [AI Research Gap Finder - Autonomous Discovery App]", flush=True)
    print(f" Application URL:  http://{host}:{port}/", flush=True)
    print(f" Interactive Docs: http://{host}:{port}/docs", flush=True)
    print("=======================================================\n", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="info")
