import os
import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core.config import Config
from backend.services.research_service import ResearchService
from backend.api.main import app
from api.index import app as vercel_app


def test_config_defaults():
    """Verify application configuration defaults and validation."""
    assert Config.validate() is True
    assert Config.LLM_PROVIDER in ["groq", "ollama"]
    assert Config.CHUNK_SIZE > 0
    assert Config.CHUNK_OVERLAP >= 0
    assert Config.TOP_K > 0
    print("  [PASS] Config defaults verified.")


def test_fastapi_instance():
    """Verify FastAPI application initializes with correct metadata."""
    assert isinstance(app, FastAPI)
    assert "AI Research Gap Finder" in app.title
    assert isinstance(vercel_app, FastAPI)
    print("  [PASS] FastAPI & Vercel entrypoint instances verified.")


def test_health_endpoint():
    """Verify system health endpoint returns 200 OK and healthy status."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "configured_model" in data
    assert "total_papers" in data
    print("  [PASS] Health endpoint /api/health returned 200 OK.")


def test_stats_endpoint():
    """Verify system stats endpoint returns status and metrics."""
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_papers" in data or "status" in data
    print("  [PASS] Stats endpoint /api/stats returned 200 OK.")


def test_reference_chunk_detection():
    """Verify heuristic reference chunk detector properly identifies citations vs text."""
    # Definite bibliography citation block
    bib_text = "References\n[1] Vaswani, A., et al. (2017). Attention is all you need. In NeurIPS, pp. 5998-6008. https://doi.org/10.1000/182"
    assert ResearchService.is_reference_chunk(bib_text) is True

    # Regular academic content chunk
    content_text = "In this work, we propose a novel multi-agent consensus framework to evaluate hypothesis validity across disparate biological literature domains."
    assert ResearchService.is_reference_chunk(content_text) is False
    print("  [PASS] Heuristic reference chunk detection verified.")


if __name__ == "__main__":
    print("\nRunning smoke tests for AI Research Gap Finder...")
    test_config_defaults()
    test_fastapi_instance()
    test_health_endpoint()
    test_stats_endpoint()
    test_reference_chunk_detection()
    print("\n All smoke tests passed successfully!\n")
