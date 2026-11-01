# KURINJI — Badaga & Marwari Audio Recognition System

An AI-powered audio recognition and translation system for low-resource languages (Badaga and Marwari) without standardized writing systems. Retrieves human-verified Tamil and English meanings from a closed-vocabulary database.

---

## Quick Setup Guide for Developers

### 1. Backend Setup (Python)
1. Open terminal in the project root:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # On Windows
   # source .venv/bin/activate # On Mac/Linux
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI backend server:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Backend will be live at: `http://127.0.0.1:8000` (API docs at `/docs`).

---

### 2. Frontend Setup (React + Vite)
1. Open a new terminal in the `frontend` folder:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open your browser at: `http://127.0.0.1:5173/`

---

### 3. Architecture & Key Folders
- `backend/app/main.py`: FastAPI server endpoints.
- `backend/app/services/recognition.py`: Recognition orchestrator (Gemini Audio AI + offline XLS-R fallback).
- `backend/app/services/gemini_recognition.py`: Gemini 3.5 Multimodal Audio AI integration.
- `backend/data/vocabulary.db`: SQLite database storing verified vocabulary entries and recordings metadata.
- `backend/data/embeddings/`: 619 pre-extracted 1024-d phonetic embeddings (.npy).
- `frontend/src/`: React UI components (ChatGPT minimalist aesthetic).
- `.env`: Configure `GEMINI_API_KEY` for high-accuracy audio recognition.
