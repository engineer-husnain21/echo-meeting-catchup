# ECHO: Voice Meeting Catch-Up (Multi-Agent)

ECHO helps a developer who missed meetings catch up by voice. Upload meeting
transcripts into a topic, then listen to a short spoken brief and ask follow-up
questions. Every answer links back to the exact transcript lines.

> Work in progress. Setup, sample data, agent design and stack choices will be
> documented here as the project is built.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env   # then fill in your own free-tier keys
python -m pytest
uvicorn app.main:app --reload
```

Health check: http://127.0.0.1:8000/api/v1/health

## Project structure

This repo follows the team's AI Project Structure Guidelines (see `CLAUDE.md`).
