# ELITE NEXUS AI — MATRIX OS PROJECT GUIDE
> Last Updated: May 23, 2026
> Status: Active Development
> Repo: https://github.com/Elite-Nexus-AI/Elite-Nexus-Matrix-Command-Center

---

## ✅ ALREADY BUILT (DO NOT REBUILD)

- Matrix HUD shell — cyberpunk interface, live at localhost:8765
- Hermes Agent + Claude Sonnet 4 via OpenRouter — full tool use
- Smart LLM Router — 6-tier model selection (vLLM → Ollama → Claude → Opus)
- vLLM — Qwen2.5-72B AWQ running across dual RTX 3090 (free local 72B)
- Gmail / Calendar / Drive / YouTube — Google Workspace fully authenticated
- Webcam vision — 📷 button in HUD
- Morning Briefing — real Gmail + Calendar via /briefing/morning endpoint
- Piper TTS — single Jenny Dioco British voice, no edge-tts
- Browser control — xdg-open via Hermes terminal tool
- YouTube playlist launcher — /playlist command + lookup table
- Watchdog — bridge auto-restarts if it dies
- Llama 3.1 70B — downloading to /mnt/data/models/
- GitHub repo — clean, no secrets

---

## 📋 REMAINING BUILD LIST — BITE-SIZE SESSIONS

---

### 🔴 SESSION 1 — Financial Telemetry Footer
**Time Estimate: 1-2 hours**
**What it does:** Shows real-time cost of every conversation in the HUD

Tasks:
- [ ] Add cost footer bar to HUD below chat window
- [ ] Track which model is being used per message (from router)
- [ ] Display: model name | tokens used | cost ($0.00 local / $X.XX cloud)
- [ ] Running daily total — red for paid, green for free local
- [ ] Hard limit warning — TTS alert when daily spend hits $X
- [ ] Session savings calculator (what vLLM saved vs OpenRouter)

Files to edit: `index.html`, `bridge.py`
New endpoint: `GET /telemetry/session`

---

### 🔴 SESSION 2 — Task Scaffolding UI (Orchestration Panel)
**Time Estimate: 2-3 hours**
**What it does:** Structured project entry — tell Matrix what to build

Tasks:
- [ ] Add "NEW PROJECT" button to HUD
- [ ] Modal with fields:
  - Task Type dropdown: Website Design, App Design, Agent Design, Super Agent, Chatbot, Voice Bot, Workflow
  - Project Name (text)
  - Brief Description (text)
  - In-Depth Description (textarea)
  - Tool Assignment: Auto or Manual (n8n, Dify, Next.js, FastAPI)
  - Build Preferences (text)
- [ ] Submit → sends structured prompt to Hermes CEO orchestrator
- [ ] Hermes generates project `.md` file to `/mnt/data/Matrix-Production/projects/`
- [ ] Show project in vault panel

Files to edit: `index.html`, `bridge.py`
New endpoint: `POST /projects/create`

---

### 🔴 SESSION 3 — Income Factory Dashboard (Real Data)
**Time Estimate: 2-3 hours**
**What it does:** Live Alpha vs Beta factory leaderboard in HUD

Tasks:
- [ ] Wire Factory Alpha + Beta panels to real SQLite data
- [ ] CFO Agent market feed — pulls trending products via web search
- [ ] Asset gallery carousel — shows latest generated assets
- [ ] Financial health meter — progress bar toward $5k/month goal
- [ ] Factory status: IDLE / RUNNING / PUBLISHING / ERROR
- [ ] Competitive reward status — winner badge
- [ ] Auto-refresh every 60 seconds

Files to edit: `index.html`, `bridge.py`
New: `factory_state.db`, `/mnt/data/ai_factory/` structure

---

### 🟡 SESSION 4 — Obsidian Bi-Directional Sync
**Time Estimate: 1-2 hours**
**What it does:** Matrix reads/writes your Obsidian vaults

Tasks:
- [ ] Scan vault at `/mnt/data/New-matrix-vault/` and `/mnt/data/Matrix-Production/`
- [ ] Display vault notes in HUD vault panel (already partially built)
- [ ] Agent generates daily summary note automatically
- [ ] Agent links unlinked mentions in vault
- [ ] New endpoint: `POST /vault/write` — write note from HUD
- [ ] New endpoint: `GET /vault/search` — semantic search in vault
- [ ] Wire to morning briefing — include relevant vault notes

Files to edit: `bridge.py`, `index.html`
New endpoints: `/vault/write`, `/vault/search`, `/vault/daily-summary`

---

### 🟡 SESSION 5 — CEO Orchestrator + Department Heads
**Time Estimate: 3-4 hours**
**What it does:** Matrix becomes a multi-agent CEO with departments

Tasks:
- [ ] Define 5 department head personas in Hermes config:
  - Product Development Head
  - Client Services & Consulting Head
  - Marketing & Growth Head
  - Cybersecurity & Compliance Head
  - CFO Agent (market analysis + factory management)
- [ ] CEO routing logic — analyzes task, assigns to correct department
- [ ] Each head spawns 3-5 sub-agents for parallel execution
- [ ] Sub-agent results reconstructed by department manager
- [ ] Add Tattletale Agent — monitors + reports underperformers
- [ ] Add Teacher Agent — maintains Obsidian knowledge bases
- [ ] Agent Commander panel wired to real spawning

Files to edit: `bridge.py`, `index.html`
New: `~/.hermes/department_heads/` persona configs

---

### 🟡 SESSION 6 — Wake Word + Global Hotkey
**Time Estimate: 1-2 hours**
**What it does:** Say "Hermes" or press hotkey to activate HUD anywhere

Tasks:
- [ ] Always-on Whisper listener for wake word "Hermes" or "Matrix"
- [ ] System-wide hotkey (e.g., Ctrl+Space) to focus HUD
- [ ] Auto-capture clipboard content when HUD is summoned
- [ ] Auto-capture active window title for context
- [ ] Feed context to Hermes automatically
- [ ] Add to autostart

New: `wake_word_listener.py`, systemd service

---

### 🟠 SESSION 7 — Factory 1: Identity POD Store
**Time Estimate: 4-6 hours**
**What it does:** Autonomous print-on-demand product generation

Tasks:
- [ ] Trend scraper — scrape Etsy/Pinterest/TikTok for niche trends
- [ ] SDXL/Flux prompt generator from trend data
- [ ] Image generation pipeline (local GPU)
- [ ] Real-ESRGAN upscaler to 300 DPI
- [ ] Printify API integration — upload as draft
- [ ] Auto-generate title, tags, description via LLM
- [ ] Log to `factory_state.db`
- [ ] Draft enforcement — never auto-publish

New: `/mnt/data/ai_factory/factories/factory_1_pod/`

---

### 🟠 SESSION 8 — Factory 2: Stream Asset Factory
**Time Estimate: 4-6 hours**
**What it does:** Automated stream overlay + Discord emote generation

Tasks:
- [ ] Niche research — Twitch/YouTube trending aesthetics
- [ ] SDXL overlay frame generation (alpha-transparent PNG)
- [ ] Stable Video Diffusion for animated overlays (4K MP4)
- [ ] Gumroad API — upload as draft listing
- [ ] Etsy API — upload as draft listing
- [ ] Auto-title + tags + description
- [ ] Log to factory state

New: `/mnt/data/ai_factory/factories/factory_2_stream/`

---

### 🟠 SESSION 9 — Factory 3+4+5 (Digital Press, Dev Lab, Vector House)
**Time Estimate: 6-8 hours**
**What it does:** Three more autonomous product factories

Factory 3 — Gothic Digital Press:
- [ ] Digital planner PDF generation (hyperlinked, iPad-ready)
- [ ] Gallery wall art packs (dark botanical, parchment textures)
- [ ] Etsy + Gumroad draft upload

Factory 4 — Developer Utility Lab:
- [ ] Notion workspace templates (JSON schema)
- [ ] LLM prompt workbooks (markdown)
- [ ] Gumroad + Notion Template Gallery upload

Factory 5 — Vector Crafting House:
- [ ] SVG generation via potrace pipeline
- [ ] Cyber-Occult geometry patterns
- [ ] Creative Market + Etsy draft upload

---

### 🔵 SESSION 10 — Iris Vault (PostgreSQL + pgvector)
**Time Estimate: 3-4 hours**
**What it does:** Local database for unlimited memory + cost ledger

Tasks:
- [ ] Spin up PostgreSQL + pgvector in Docker
- [ ] Create TokenLedger table (model, tokens, cost, timestamp)
- [ ] Create SecurityAuditLog table (action, category, user_approved)
- [ ] Create ProjectMemory table (project_id, context, blueprint)
- [ ] Wire bridge to log all LLM calls to TokenLedger
- [ ] Connect to financial telemetry footer
- [ ] RAG search over Obsidian vault content

New: `docker-compose-iris.yml`, `iris_vault.py`

---

### 🔵 SESSION 11 — Zero-Trust Security Matrix
**Time Estimate: 3-4 hours**
**What it does:** Traffic light permission system for agent actions

Tasks:
- [ ] Categorize all agent actions: Green / Yellow / Red
- [ ] Green → auto-proceed (reads, calculations)
- [ ] Yellow → notify in HUD, proceed after 3 seconds
- [ ] Red → HITL interrupt — approval button appears in HUD
- [ ] Git snapshot before every Red action
- [ ] One-click rollback from HUD
- [ ] Log all actions to SecurityAuditLog in Iris Vault
- [ ] Plain-English audit timeline panel in HUD

Files to edit: `bridge.py`, `index.html`

---

### 🔵 SESSION 12 — Semantic Screen Awareness
**Time Estimate: 2-3 hours**
**What it does:** Matrix sees your screen without you telling her

Tasks:
- [ ] OCR running on active window (Tesseract or EasyOCR)
- [ ] Screenshot → text every 30 seconds
- [ ] Feed relevant context to Hermes automatically
- [ ] Contextual Awareness Dashboard panel in HUD
- [ ] Shows: active window, clipboard, relevant Obsidian notes
- [ ] Matrix proactively comments on what she sees

New: `screen_awareness.py`, systemd timer

---

### 🔵 SESSION 13 — n8n + Dify Docker Sandbox
**Time Estimate: 2-3 hours**
**What it does:** Local workflow builder + RAG system

Tasks:
- [ ] Spin up n8n in Docker (port 5678)
- [ ] Spin up Dify in Docker (port 3000)
- [ ] Hermes can create n8n workflows via API
- [ ] Hermes can create Dify knowledge bases via API
- [ ] Visual server rack representation in HUD

New: `docker-compose-sandbox.yml`

---

### 🔵 SESSION 14 — Idle Dreaming Mode
**Time Estimate: 3-4 hours**
**What it does:** Matrix self-improves while you're away

Tasks:
- [ ] Detect user idle (no input for 15+ minutes)
- [ ] Trigger Dreaming mode — subtle HUD animation
- [ ] Hermes simulates complex builds in latent space
- [ ] Zero token cost — uses local vLLM only
- [ ] New skills logged to Recursive Skill Ledger
- [ ] Skill Ledger panel in HUD — inspectable, clickable entries
- [ ] Natural language skill creation: "teach yourself X"
- [ ] Morning briefing includes overnight dream summary

New: `dream_engine.py`, skill ledger SQLite

---

### 🔵 SESSION 15 — Tauri Desktop App Wrapper
**Time Estimate: 4-6 hours**
**What it does:** Turns HUD into native desktop app

Tasks:
- [ ] Init Tauri 2.0 project wrapping current HTML/JS
- [ ] Configure transparent click-through overlay
- [ ] tRPC for frontend/Rust communication
- [ ] Rust Resource Governor — throttle HUD during heavy inference
- [ ] Predictive resource allocation
- [ ] sysinfo Rust bindings for OS metrics
- [ ] enigo for system automation
- [ ] Rust keyring for encrypted credential storage
- [ ] Replace config.sh secrets with keyring

New: `src-tauri/` directory, full Rust backend

---

### 🔵 SESSION 16 — Virtual Agent Office (3D)
**Time Estimate: 6-8 hours**
**What it does:** 3D office where you see agents working

Tasks:
- [ ] React Three Fiber 3D environment
- [ ] Drag-and-drop office layout (desks, server racks, decorations)
- [ ] 3D avatars for Hermes, Claude, department heads
- [ ] Avatars animate with agent execution states
- [ ] Server racks pulse when Docker containers active
- [ ] Holographic factory production line view
- [ ] Dynamic avatar spawning for new sub-agents
- [ ] Skill Store UI — browse/install skills

New: Full 3D React component, replaces current vault panel

---

## 🗺️ RECOMMENDED BUILD ORDER

```
Session 1  → Financial Telemetry Footer      (quick win, visible)
Session 2  → Task Scaffolding UI             (core UX upgrade)
Session 3  → Income Factory Dashboard        (money engine)
Session 4  → Obsidian Sync                   (knowledge base)
Session 5  → CEO Orchestrator + Departments  (agent brain)
Session 6  → Wake Word + Hotkey              (UX polish)
Session 7  → Factory 1 POD                  (revenue)
Session 8  → Factory 2 Stream Assets        (revenue)
Session 9  → Factory 3+4+5                  (revenue)
Session 10 → Iris Vault Database             (foundation)
Session 11 → Security Matrix                 (safety)
Session 12 → Screen Awareness               (intelligence)
Session 13 → n8n + Dify Sandbox             (builder tools)
Session 14 → Idle Dreaming                  (self-improvement)
Session 15 → Tauri Desktop App              (production)
Session 16 → Virtual Agent Office 3D        (showcase)
```

---

## 📁 PROJECT FILE STRUCTURE

```
~/Downloads/files/matrix-hud-perfect/
├── bridge.py              ← FastAPI backend (main server)
├── index.html             ← Matrix HUD frontend
├── llm_router.py          ← Smart LLM routing logic
├── start_vllm.sh          ← Launch Qwen2.5-72B on dual 3090
├── start-matrix.sh        ← Full system startup
├── config.sh              ← API keys + env vars (gitignored)
├── watchdog.sh            ← Bridge auto-restart
├── bridge.py.golden       ← Last known good backup
├── index.html.golden      ← Last known good backup

/mnt/data/
├── models/
│   ├── Qwen2.5-72B-Instruct-AWQ/   ← Primary vLLM model (39GB)
│   ├── Qwen2.5-72B-Instruct/        ← Full precision (136GB)
│   └── Llama-3.1-70B-Instruct/     ← Downloading...
├── ai_factory/                      ← Factory engine (Session 3+)
│   ├── core_orchestrator.sh
│   ├── factory_state.db
│   ├── shared_modules/
│   └── factories/
├── Matrix-Production/               ← Obsidian vault (production)
└── New-matrix-vault/                ← Obsidian vault (notes)
```

---

## 🔑 KEY CREDENTIALS & SERVICES

| Service | Status | Notes |
|---------|--------|-------|
| OpenRouter API | ✅ Active | Key in config.sh |
| Claude Code MAX | ✅ Active | info@elitenexusai.com |
| Google Workspace | ✅ Authenticated | Gmail, Calendar, Drive, YouTube |
| HuggingFace | ✅ Active | Matrix-Hermes token |
| vLLM | ✅ Running | Port 8000, Qwen2.5-72B AWQ |
| Ollama | ✅ Running | Port 11434, qwen3.5:27b |
| Matrix Bridge | ✅ Running | Port 8765 |
| Piper TTS | ✅ Active | Jenny Dioco British voice |

---

## ⚡ QUICK START (After Reboot)

```bash
cd ~/Downloads/files/matrix-hud-perfect
source config.sh
# Stop Kokoro Docker (frees GPU 0 VRAM)
sudo docker stop $(sudo docker ps -q --filter "publish=8880") 2>/dev/null
# Start vLLM (72B local model)
bash start_vllm.sh &
# Start bridge
source .venv/bin/activate
python3 bridge.py >> /tmp/matrix-bridge.log 2>&1 &
# Open HUD
xdg-open http://localhost:8765
```

---

*This document is the master project guide for Elite Nexus AI Matrix OS.*
*Update this file after completing each session.*
