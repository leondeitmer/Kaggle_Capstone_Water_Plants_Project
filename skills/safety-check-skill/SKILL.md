---
name: safety-check-skill
description: Chat‑only safety‑check guidelines. Use during reviews to ensure no hard‑coded API keys, absolute paths, passwords, or other secrets are present in the repository.
---

# Safety‑Check Skill (Chat‑Only)

**Purpose**: Provide a quick checklist for the human‑in‑the‑loop (us) to run a manual security scan before committing or sharing code. This skill is **not** executed by the runtime agents; it is only for conversational verification.

## Checklist
1. **Relative Paths Only**
   - Verify that all file references in code, documentation, and configuration use relative paths (e.g., `../resources/plant_database.json`).
   - Absolute Windows paths like `C:\\Users\\leond\\...` must be replaced with project‑relative equivalents.
2. **API Keys / Secrets**
   - Search for patterns such as `*_KEY=`, `*_TOKEN=`, `password`, `secret`, `credential`, `access_key`, `aws_secret`.
   - Ensure any secret values live **only** in the `.env` file and that `.env` is listed in `.gitignore`.
   - If a secret appears in source code, flag it and move it to `.env` (or a secret manager).
3. **Password‑like Strings**
   - Look for any string that resembles a password (>= 8 characters, mixed case/symbols) even if not labelled as a key.
4. **Git‑Tracked Sensitive Files**
   - Run `git ls-files --error-unmatch .env` to confirm `.env` is not tracked.
   - Ensure other credential files (e.g., `credentials.json`) are also ignored.
5. **Hard‑Coded URLs with Tokens**
   - Verify URLs do not embed tokens or API keys as query parameters.

## How to Apply in Chat
- When reviewing a PR or a new file, copy‑paste the file content into the chat and ask the assistant to run a **Safety‑Check** using the checklist above.
- The assistant will list any violations and suggest remediation steps.

## Example Prompt
```
Please run the Safety‑Check on the following file:
```markdown
<file content>
```
```
The assistant should respond with any detected issues and recommendations.

---
**Note**: This skill is purely informational and does not affect runtime behavior. It is intended for human‑review during development and CI discussions.
