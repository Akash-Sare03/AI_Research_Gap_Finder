# AI Research Gap Finder & Autonomous Discovery

[![CI/CD Pipeline](https://github.com/your-username/AI_Research_Gap_Finder/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-username/AI_Research_Gap_Finder/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Groq API](https://img.shields.io/badge/Groq-Ultra--Fast%20Inference-f55036.svg)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-orange.svg)](https://www.trychroma.com)

An AI-powered Academic Research Assistant and Multi-Agent Scientific Discovery platform. Upload any research paper (PDF) to instantly extract research gaps, run grounded RAG question-answering, explore interactive 60 FPS knowledge galaxies, and execute a 5-agent autonomous discovery pipeline with live debate and self-correction.

---

## 🌟 Key Features

### 1. 🤖 5-Agent Autonomous Scientific Discovery
A multi-agent Actor-Critic orchestration engine that works through five distinct specialized stages:
1. **Concept Mapper**: Extracts semantic entities, foundational axioms, and relationship links from the paper text.
2. **Idea Theorist**: Formulates radical, new-to-the-world scientific breakthrough hypotheses not found in the original paper.
3. **Peer Referee**: Acts as an adversarial reviewer to challenge the hypothesis, stress-testing boundary conditions and failure modes.
4. **Self-Correction Lead**: Refines the breakthrough to resolve all objections with defensive constraints and mathematical rigor.
5. **Blueprint Architect**: Creates a verified 3-phase testing roadmap with actionable experiments, metrics, and falsification confidence scoring.

### 2. 🌌 Interactive Knowledge Galaxy (60 FPS Simulation)
- Dynamic Canvas galaxy connecting base paper concepts with AI-discovered breakthrough nodes.
- Animated laser energy beams showing the real-time reasoning flow between agents.
- Interactive step cards with click-to-open modals for in-depth reasoning, mathematical formulations, and validation protocols.

### 3. 🔍 9-Section Academic Research Gap Analysis
Automatically breaks down any research paper into:
- Executive Summary & Problem Formulation
- Core Contributions & Novelty Assessment
- Methodological Limitations & Assumptions
- Unexplored Edge Cases & Negative Constraints
- 5 Concrete Research Gaps with Proposed Future Solutions

### 4. 💬 Grounded RAG Question Answering
- Chat with your research paper with zero hallucination.
- Every claim is cited directly with exact source snippets and page/chunk references.
- Pre-built quick prompt suggestions for common questions.

### 5. 🌐 Online Literature Comparison
- Searches external databases to find related academic papers.
- Generates side-by-side comparative reviews and positioning analysis.

### 6. 📄 1-Click Multi-Format Report Export
- Download comprehensive research gap reports in **PDF**, **Markdown**, or **JSON** format.

### 7. 🔒 Secure Authentication & Free Guest Trials
- **12 Free Guest Preview Trials** out-of-the-box using the built-in system key.
- Google OAuth & Email authentication.
- Scoped user workspace isolation (your uploaded papers remain private to your account).
- Bring-Your-Own-Key support for unlimited PhD-level research using free Groq API keys.

---

## 🏗️ Architecture & Technology Stack

```
AI_Research_Gap_Finder/
├── backend/
│   ├── api/             # FastAPI REST endpoints & route handlers
│   ├── core/            # Authentication, JWT, Quota tracker, Config, LLM service
│   ├── document/        # PDF extraction, cleaning & recursive chunking
│   ├── vectorstore/     # ChromaDB vector store & hybrid search
│   ├── analysis/        # Autonomous discovery engine, novelty auditor, metrics extractor
│   └── services/        # Orchestration layer for research workflows
├── frontend/
│   ├── index.html       # Single-page modern application UI
│   ├── style.css        # Academic dark-theme UI with 60 FPS animations
│   └── app.js           # Vanilla JS controller (Zero build step needed)
├── .github/workflows/   # Automated CI/CD GitHub Actions pipeline
├── render.yaml          # Render Blueprint deployment configuration
├── requirements.txt     # Python production dependencies
└── run_app.py           # Single-command launcher for local & cloud servers
```

- **Backend**: FastAPI, Uvicorn, LangChain, Groq API (`qwen/qwen3.8-27b`), ChromaDB, HuggingFace Sentence-Transformers (`all-MiniLM-L6-v2`), ReportLab.
- **Frontend**: Modern Vanilla HTML5, CSS3 Glassmorphism, FontAwesome 6, Canvas 2D.
- **Deployment**: Render, Docker-ready, GitHub Actions CI/CD.

---

## 🚀 Quick Start Guide (Local Setup)

### Prerequisites
- Python 3.11+ installed ([Download Python](https://www.python.org/downloads/))
- Free Groq API Key ([Get a free key at console.groq.com](https://console.groq.com))
- Git installed ([Download Git](https://git-scm.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/AI_Research_Gap_Finder.git
cd AI_Research_Gap_Finder
```

### 2. Create and Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (or copy from `.env.example`):
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and paste your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=qwen/qwen3.8-27b
```

### 5. Launch the Application
```bash
python run_app.py
```

Open your browser and navigate to:
👉 **`http://localhost:8000`** (or **`http://127.0.0.1:8000`**)
Interactive API Swagger Docs: **`http://localhost:8000/docs`**

---

## 🌐 Step-by-Step Render Cloud Deployment Guide

You can deploy this application for free on [Render](https://render.com) in under 5 minutes:

### Step 1: Push Your Code to GitHub
1. Create a new repository on [GitHub](https://github.com/new) (e.g., `AI_Research_Gap_Finder`).
2. Push your local files to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: AI Research Gap Finder with Autonomous Multi-Agent Discovery"
   git branch -M main
   git remote add origin https://github.com/your-username/AI_Research_Gap_Finder.git
   git push -u origin main
   ```

### Step 2: Create a Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** ➔ **Web Service**.
2. Connect your GitHub repository: `AI_Research_Gap_Finder`.
3. Configure the service settings:
   - **Name**: `ai-research-gap-finder`
   - **Environment**: `Python`
   - **Region**: `Oregon (US West)` (or closest to you)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run_app.py`
   - **Instance Type**: `Free`

### Step 3: Add Environment Variables in Render
In the **Environment Variables** tab of your Render service, add:
| Key | Value | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `gsk_...` | Your Groq API key from console.groq.com |
| `LLM_MODEL` | `qwen/qwen3.8-27b` | Recommended fast inference model |
| `PYTHON_VERSION` | `3.11.9` | Python runtime version |
| `TOKENIZERS_PARALLELISM` | `false` | Prevents sub-process deadlocks |
| `ANONYMIZED_TELEMETRY` | `False` | Disables telemetry overhead |

### Step 4: Deploy & Access Live URL
Click **Create Web Service**. Render will automatically build and deploy your application. Within 2-3 minutes, your live URL will be active:
👉 `https://ai-research-gap-finder.onrender.com`

---

## 🔄 CI/CD Pipeline with GitHub Actions

This repository includes a `.github/workflows/ci-cd.yml` workflow:

1. **Automated Testing & Linting**: Runs on every push and pull request to `main`.
   - Validates Python syntax with `flake8`.
   - Tests FastAPI application startup and endpoint dependencies.
2. **Auto-Deployment to Render**:
   - (Optional) In your Render Web Service settings, copy your **Deploy Hook URL**.
   - Go to your GitHub Repository ➔ **Settings** ➔ **Secrets and variables** ➔ **Actions**.
   - Add secret named `RENDER_DEPLOY_HOOK_URL`.
   - Every time you push changes to `main`, GitHub Actions will test the code and trigger an instant deployment on Render.

---

## 🛡️ Exception Handling & Production Reliability

- **PDF Error Protection**: Validates headers (`%PDF-`), file size limits (50MB), and handles scanned or encrypted files cleanly.
- **Deduplication Engine**: Uses SHA-256 file hashing to prevent duplicate uploads and redundant LLM token costs.
- **Smart Quotas & Fallbacks**: Graceful rate limit notifications (`HTTP 429`) with guidance on setting a custom API key.
- **Offline Resilience**: Detects network connectivity changes and alerts users via clean toast notifications.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 💡 Acknowledgements
- [Groq](https://groq.com/) for ultra-fast LPU inference.
- [FastAPI](https://fastapi.tiangolo.com/) for high-performance Python backend architecture.
- [ChromaDB](https://www.trychroma.com/) for lightweight, persistent vector embeddings.
- [HuggingFace](https://huggingface.co/) for open-source embedding models.
