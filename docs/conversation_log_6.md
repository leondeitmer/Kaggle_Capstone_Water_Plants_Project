# Conversation Log 6: ADK Playground Integration & Git Workflow

**Date:** June 27, 2026  
**Participants:** User & Antigravity (AI Coding Assistant)  
**Topic:** Launch of local development playground, integration of agents-cli ADK playground, debugging, safety check execution, and git commit workflow with new skill.

---

## 1. Local Dev Playground Launch (Frontend + Backend)

On session start, both the FastAPI backend and Vite frontend were launched for local development testing.

**Backend (FastAPI/Uvicorn):**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- Serves the `/api/analyze` endpoint, orchestrating the MCP geocoding + weather pipeline and Gemini analysis.

**Frontend (Vite Dev Server):**
```bash
npm.cmd run dev
# → http://localhost:5173/
```
- The frontend was subsequently stopped after the user switched focus to the `agents-cli` playground.

---

## 2. agents-cli Playground — Setup & Error Diagnosis

### 2.1 Objective
The user asked to run `agents-cli playground`, the standard dev tool from the Google Agents CLI.

### 2.2 Problem: Missing Manifest File
Running `agents-cli playground` in the project root failed immediately:
```
Error: No agents-cli-manifest.yaml found in the current directory or its parents.
```
The main project codebase does not use the **Google ADK** (`google-adk`) framework — it uses `google-genai` directly with FastAPI. The `agents-cli` requires an ADK-structured project with a manifest file.

### 2.3 Solution: Scaffold a New ADK Agent
A new ADK project scaffold was created via:
```bash
agents-cli create floracast-agent --adk -y
```
This created `floracast-agent/` with the required:
- `agents-cli-manifest.yaml`
- `app/agent.py` — Standard ADK Agent using `google.adk.agents.Agent`
- `pyproject.toml` and `uv.lock`
- Deployment Terraform templates

Dependencies were installed via:
```bash
agents-cli install   # calls uv sync, installs 148 packages
```

### 2.4 Playground Start
```bash
agents-cli playground
# → http://127.0.0.1:8080/dev-ui/?app=app
```
Internally runs: `uv run adk web . --host 127.0.0.1 --port 8080 --allow_origins "*"`

---

## 3. Bug Fix: Agent Module Import Crash (TypeError: str expected, not NoneType)

### 3.1 Root Cause
The generated `app/agent.py` template attempted to resolve a Google Cloud project ID at module load time:
```python
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id  # ← TypeError when project_id is None
```
Without a configured GCP project locally, `google.auth.default()` returns `project_id = None`, which cannot be assigned to an environment variable — causing the module to fail to import. The playground API then returned HTTP 500 errors on every request.

### 3.2 Fix Applied in `floracast-agent/app/agent.py`
```python
try:
    _, project_id = google.auth.default()
except Exception:
    project_id = None

if project_id:
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
```
Additionally, the model was updated from `"gemini-flash-latest"` to `"gemini-2.5-flash"` to ensure AI Studio compatibility.

### 3.3 Verification
After restarting the playground, the agent correctly responded to chat queries by executing the simulated tools:
- Input: *"How is the weather in San Francisco?"*
- Tool call: `get_weather("San Francisco")`
- Response: *"It's 60 degrees and foggy."*

---

## 4. Safety Check Execution

A full safety check was performed on the repository using the `safety-check-skill`:

| Check | Result | Notes |
|---|---|---|
| Relative Paths in Source | ✅ Pass | No absolute Windows paths in tracked source files |
| API Keys in Source Code | ✅ Pass | `GEMINI_API_KEY` is only read via `os.environ.get()` |
| `.env` not tracked by Git | ✅ Pass | Confirmed absent from `git ls-files` |
| Passwords in Source | ✅ Pass | None found |
| Token-embedded URLs | ✅ Pass | No `?api_key=` or `?token=` in any URL |
| `.env.example` clean | ✅ Pass | Contains only `your_gemini_api_key_here` placeholder |

**⚠️ Advisory**: The `.env` file contains a real `GEMINI_API_KEY`. It is not git-tracked, but rotating the key periodically is recommended as a security best practice.

---

## 5. New Skill: `git-commit-version`

A new skill was created at `skills/git-commit-version/` to standardize commit naming and enforce pre-commit safety checks.

### 5.1 Commit Naming Convention

| Type | Format | Example |
|---|---|---|
| Normal commit | `<type>: <description>` | `docs: add safety-check skill` |
| Breaking/Special | `! <description>` | `! Add ADK playground agent with local Gemini API fallback` |

### 5.2 Pre-Commit Safety Checks (Automated)

The script `skills/git-commit-version/scripts/safe_commit.py` performs the following checks on **staged changes** before every commit:
1. **Absolute Paths**: Rejects commits containing Windows absolute paths (e.g., `C:\Users\<username>\...`).
2. **Hardcoded API Keys**: Scans for patterns like `GEMINI_API_KEY="AQ..."` in added lines.
3. **`.env` tracking**: Aborts if `.env` is tracked by Git.

**Usage:**
```bash
python skills/git-commit-version/scripts/safe_commit.py "commit message"
python skills/git-commit-version/scripts/safe_commit.py "! breaking change" --breaking
```

If any check fails, the script prints a warning and exits without committing.

### 5.3 Skill Test — Pre-Commit Safety Check in Action
During creation of the skill itself, the script correctly caught an issue:
- The `SKILL.md` contained a documentation example with a user-specific path (`C:\Users\<username>\...`).
- The safety check triggered a warning and aborted the commit.
- After replacing the path with `C:\Users\<username>\...`, the checks passed and the commit succeeded.

---

## 6. Commits This Session

| Hash | Message | Type |
|---|---|---|
| `e3d3177` | `! Add ADK playground agent (floracast-agent) with local Gemini API fallback` | Breaking/Special |
| `a172df2` | `docs: add git-commit-version skill with pre-commit safety check` | Docs |

Both commits were pushed to `origin/master` at the end of the session:
```bash
git push origin master
# To https://github.com/leondeitmer/Kaggle_Capstone_Water_Plants_Project.git
#    ee14037..a172df2  master → master
```

---

## 7. Revision History
| Date | Author | Change |
|------|--------|--------|
| 2026-06-27 | Antigravity | Initial creation covering ADK playground, bug fix, safety check, and git-commit-version skill |
