# Open CTRL+SPACE in VS Code and run it with Claude Code

## 1. Install (once)
- **Python 3.11 or newer**: python.org (Windows: tick “Add python.exe to PATH”).
- **VS Code**: code.visualstudio.com.
- **Claude Code extension**: in VS Code press Ctrl+Shift+X (Cmd+Shift+X on Mac), search “Claude Code”, check the publisher is **Anthropic** (`anthropic.claude-code`), click Install, then sign in from its panel. The project also recommends it automatically when you open the folder.
- Optional, for `claude` in the terminal: the extension has its own copy for its chat panel; the terminal command needs the standalone install from the official setup page (code.claude.com/docs → Setup).
- Optional, for browser tests on Windows: Git Bash or WSL (the desktop E2E script is bash).

## 2. Open the project
1. Unzip `CTRL_SPACE_FINAL_PROJECT.zip`.
2. VS Code → File → Open Folder → choose the **`ctrl-space`** folder (it contains `run.py` and `CLAUDE.md`).
3. Accept “Install recommended extensions” and “Trust the authors”.

## 3. Set up and run (Terminal → Run Task…)
1. **1. Setup: create venv + install requirements**
2. **2. Setup: install Chromium for browser tests** (optional)
3. **3. Setup: create .env from template**
4. **4. Create admin account** (asks for email and name, then a password)
5. **Run: CTRL+SPACE server** → open http://127.0.0.1:8000 (website) and http://127.0.0.1:8000/app (mobile app)

Or press F5 → “CTRL+SPACE server (debug)” to run with breakpoints. Tests: Terminal → Run Task → “Test: …”, or the Testing panel (beaker icon).

## 4. Work with Claude Code
Open the Claude Code panel (spark icon). It reads `CLAUDE.md` automatically, so it knows the project, the rules and the commands. Useful first prompts:
- “Read CLAUDE.md and docs/MASTER_CHECKLIST.md, then run the backend tests and tell me the results.”
- “Start the server and run the mobile app tests against it.”
- “Configure Anthropic as the AI provider using my key in .env, run check-ai, then ask the 12 evaluation questions and report which answers cite correctly.”
- “Implement stop-generation in the mobile assistant, add tests, and update MASTER_CHECKLIST.md.”

## 5. Phone, APK and iOS
- Phone on the same Wi-Fi: `http://<your-computer-IP>:8000/app` (start the server with `run.py serve --host 0.0.0.0`).
- Install as an app / build APK and iOS: `docs/NATIVE_BUILDS.md`.
