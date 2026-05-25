# ELITE NEXUS AI — MATRIX OS MASTER PROJECT GUIDE v3
> Last Updated: May 25, 2026
> Repo: https://github.com/Elite-Nexus-AI/Elite-Nexus-Matrix-Command-Center
> Revenue Target: $10,000–$20,000/month autonomous factories
> Status: Phase 0 Complete — Phase 1 Next

---

## SYSTEM SPECS
- OS: Zorin OS 18 (Ubuntu base) · Username: matrix
- CPU: Intel Core i9
- GPU: 2× NVIDIA RTX 3090 (48GB combined VRAM)
- RAM: 128GB · Storage: 250GB OS SSD + 8TB Data SSD (/mnt/data)

---

## ✅ PHASE 0 — FACTUALLY BUILT AND CONFIRMED WORKING

| Component | Status | Location |
|-----------|--------|----------|
| Matrix HUD | ✅ LIVE | localhost:8765 · index.html + bridge.py |
| Hermes Agent + Claude Sonnet 4 | ✅ LIVE | ~/hermes-agent/cli.py · OpenRouter |
| Smart LLM Router | ✅ LIVE | llm_router.py · 6-tier routing |
| vLLM Qwen2.5-72B AWQ | ✅ LIVE | /mnt/data/models/Qwen2.5-72B-Instruct-AWQ |
| Google Workspace Auth | ✅ LIVE | ~/.hermes/google_token.json |
| Gmail / Calendar / Drive | ✅ LIVE | Hermes google-workspace skill |
| YouTube readonly scope | ✅ LIVE | Added this session |
| Morning Briefing | ✅ LIVE | POST /briefing/morning |
| Webcam Vision | ✅ LIVE | GET /webcam/capture + POST /webcam/analyze |
| Piper TTS (Jenny Dioco) | ✅ LIVE | en_GB-jenny_dioco-medium.onnx |
| Edge-TTS disabled | ✅ FIXED | no_tts instruction in persona system prompt |
| Browser control | ✅ LIVE | xdg-open + DISPLAY/DBUS env vars |
| YouTube Playlist Launcher | ✅ LIVE | /playlist command + lookup table |
| Watchdog auto-restart | ✅ LIVE | /tmp/watchdog.sh |
| GitHub repo | ✅ LIVE | github.com/Elite-Nexus-AI/Elite-Nexus-Matrix-Command-Center |
| Direct API routing (vLLM/Ollama) | ✅ LIVE | No Hermes CLI for local models |
| Llama 3.1 70B | ⏳ DOWNLOADING | /mnt/data/models/Llama-3.1-70B-Instruct/ |

### Vault Paths
- Daily notes / knowledge: /mnt/data/New-matrix-vault/
- Production / projects: /mnt/data/Matrix-Production/

### Quick Start After Reboot
```bash
cd ~/Downloads/files/matrix-hud-perfect && source config.sh
sudo docker stop $(sudo docker ps -q --filter "publish=8880") 2>/dev/null
sudo systemctl stop ollama
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
bash start_vllm.sh &
# After ~2 min when vLLM loads:
sudo systemctl start ollama
source .venv/bin/activate
python3 bridge.py >> /tmp/matrix-bridge.log 2>&1 &
xdg-open http://localhost:8765
```

---

## 🏢 ELITE NEXUS AI SERVICES & DEPARTMENT HEAD MAP

Each service line has one Department Head Agent with up to 10 sub-agents working under them.
Department Heads use local vLLM (free) for sub-tasks and only escalate to Claude when needed.

### SERVICE 1 — Smart AI Websites
**Department Head:** WEBSITE ARCHITECT
Sub-agents (up to 10): UI/UX Designer, Frontend Dev, Backend Dev, SEO Optimizer,
  Content Writer, Performance Analyst, CMS Integrator, Animation Specialist, QA Tester, DevOps
Responsibilities: Design and build adaptive AI-powered websites, landing pages, portfolio sites
Tools: Claude Code, Next.js, Tailwind, Framer Motion, Vercel deployment
Vault: /Matrix-Production/projects/websites/

### SERVICE 2 — AI Chatbots
**Department Head:** CHATBOT ENGINEER
Sub-agents (up to 10): Conversation Designer, Training Data Specialist, Integration Dev,
  Persona Writer, Flow Architect, QA Tester, Analytics Agent, CRM Connector, Escalation Handler, Deployment
Responsibilities: Design, train, and deploy AI chatbots for client websites
Tools: Dify, n8n, Hermes, OpenRouter, RAG pipelines
Vault: /Matrix-Production/projects/chatbots/

### SERVICE 3 — Voice Bots & IVR Systems
**Department Head:** VOICE SYSTEMS ENGINEER
Sub-agents (up to 10): Script Writer, Voice Persona Designer, SIP/VoIP Integrator,
  Call Flow Architect, VAPI/Retell Connector, Twilio Dev, QA Tester, Analytics, Escalation, Deployment
Responsibilities: Build outbound/inbound voice agents, IVR phone systems, telephony automation
Tools: VAPI, Retell, Twilio, Piper TTS, Whisper STT, SIP protocol
Vault: /Matrix-Production/projects/voicebots/

### SERVICE 4 — AI Agents & Super Agents
**Department Head:** AGENT ARCHITECT
Sub-agents (up to 10): Tool Specialist, Memory Systems Dev, Orchestration Designer,
  API Connector, Context Manager, Performance Monitor, Security Auditor, Test Runner, Documenter, Deployer
Responsibilities: Design and deploy single AI agents and Super Agent clusters (cognitive clusters)
Tools: LangGraph, Hermes, Claude Code, MCP plugins, vLLM
Vault: /Matrix-Production/projects/agents/

### SERVICE 5 — AI Workflows & Automation
**Department Head:** AUTOMATION ENGINEER
Sub-agents (up to 10): Process Mapper, n8n Builder, Dify Pipeline Dev,
  API Integrator, Data Transformer, Scheduler, Error Handler, Documentation Writer, QA, Deployer
Responsibilities: Build end-to-end autonomous workflow systems for business automation
Tools: n8n, Dify, Claude Code, Python, REST APIs
Vault: /Matrix-Production/projects/workflows/

### SERVICE 6 — AI Consulting & ROI Reporting
**Department Head:** AI CONSULTANT
Sub-agents (up to 10): Business Analyst, ROI Calculator, Research Agent,
  Report Writer, Presentation Builder, Data Visualizer, Strategy Agent, Competitor Analyst, Market Researcher, Client Liaison
Responsibilities: Analyze client businesses, identify AI opportunities, produce ROI reports
Tools: Web search, Claude Sonnet 4, Hermes, Google Sheets, Drive
Vault: /Matrix-Production/projects/consulting/

### SERVICE 7 — Marketing & Social Media
**Department Head:** MARKETING HEAD
Sub-agents (up to 10): Content Strategist, Copywriter, Social Media Manager,
  SEO Specialist, Ad Campaign Builder, Trend Researcher, Brand Voice Agent, Video Script Writer, Analytics, Scheduler
Responsibilities: Social media campaigns, content creation, marketing automation
Tools: Web search, CFO Agent trend data, Claude, image generation
Vault: /Matrix-Production/projects/marketing/

### SERVICE 8 — Cybersecurity & Compliance (Shield)
**Department Head:** SECURITY HEAD
Sub-agents (up to 10): Vulnerability Scanner, Compliance Checker, Audit Logger,
  Threat Analyst, Access Controller, Code Reviewer, Policy Writer, Incident Responder, Training Agent, Reporter
Responsibilities: Security audits, compliance checks, Shield Agent deployment, Sentinel monitoring
Tools: Security gate hooks, audit logs, Iris Vault, AppArmor
Vault: /Matrix-Production/projects/security/

### CFO AGENT — Financial Strategy & Income Factories
**Reports to:** CEO (Hermes/Matrix)
Sub-agents (up to 10): Trend Researcher, Market Analyst, Factory Monitor (Alpha),
  Factory Monitor (Beta), Revenue Tracker, Pricing Optimizer, Platform Health Monitor, A/B Test Runner,
  Competitor Spy, Report Generator
Responsibilities: Manage all 5 income factories, track revenue, optimize pricing, research trends
Tools: trend_scraper.py, factory_state.db, Etsy/Printify/Gumroad APIs, web search
Vault: /Matrix-Production/projects/cfo/

### CEO ORCHESTRATOR — Hermes/Matrix
Delegates all service work to department heads. Routes tasks by complexity and service type.
Implements HITL security gates for destructive actions.
Runs LangGraph supervisor loop.

---

## 📥 KNOWLEDGE INGESTOR — DRAG & DROP SYSTEM (NEW)

### What It Does
A drag-and-drop zone in the HUD where you drop:
- Text files (.txt, .md, .pdf)
- Web page URLs (paste or drag link)
- Documents (.docx, .pdf)

The agent reads the content, chunks it intelligently, and saves it to the appropriate
Obsidian vault as structured knowledge that any agent can later recall and learn from.

### Processing Pipeline
1. File/URL dropped into HUD ingestor zone
2. Content extracted (text, PDF parse, web fetch)
3. AI reads and identifies: topic, type, key concepts
4. Content chunked into 400-500 line segments max
5. Each chunk titled and indexed by topic
6. Chapters written as separate Obsidian files
7. Master index file created linking all chapters
8. Saved to selected knowledge vault
9. Agent that receives a task automatically loads relevant KB chunks

### Chunk Format (Obsidian files)
```
/knowledge/[topic-name]/
  00_index.md           ← Master index + summary
  01_overview.md        ← Chapter 1
  02_core-concepts.md   ← Chapter 2
  03_implementation.md  ← Chapter 3
  ...
  NN_[topic].md         ← As many as needed
```

### Skill: knowledge_ingestor
```python
# New skill file: ~/.hermes/skills/knowledge/knowledge_ingestor/
# Tools:
#   - ingest_file(path) → chunks + saves to vault
#   - ingest_url(url) → fetches + chunks + saves
#   - ingest_text(text, topic) → chunks + saves
#   - search_knowledge(query) → returns relevant chunks
#   - list_knowledge() → all indexed topics
```

### Vault Assignment for Ingestor
- Factual references / research → /New-matrix-vault/knowledge/
- Client/project knowledge → /Matrix-Production/projects/[service]/kb/
- Agent skill knowledge → /New-matrix-vault/skills/
- Market/trend research → /Matrix-Production/projects/cfo/research/

### What This Enables
- Drop in a competitor's website → agent learns their positioning
- Drop in a technical PDF → agent becomes expert on that topic
- Drop in a client's documents → agent understands their business before the call
- Drop in research papers → agents cite real facts instead of hallucinating
- Agents load relevant KB chunks before every task automatically

---

## 📋 COMPLETE BUILD PLAN — ALL PHASES

---

### 🔴 PHASE 1 — INTELLIGENCE LAYER (Sessions 1–5)

**S1 — Financial Telemetry Footer**
Real-time cost bar in HUD. Shows model | tokens | $cost per message.
Daily total with hard limit + TTS alert. Local savings vs paid.
New endpoint: GET /telemetry/session

**S2 — Task Scaffolding UI**
New Project modal. Dropdown: 8 service types (from service list above).
Fields: Name, Brief, In-Depth, Tools, Build Preferences.
Submit → CEO generates project .md to vault.
New endpoint: POST /projects/create

**S3 — Obsidian Bi-Directional Sync**
Read/write /mnt/data/New-matrix-vault/ and /mnt/data/Matrix-Production/
Agent generates daily summary notes. Vault search endpoint.
New endpoints: /vault/write, /vault/search, /vault/daily-summary

**S4 — Chat Persistence + Agent Switcher**
SQLite chat_messages table: sessionId, role, content, persona, model, cost, timestamp.
Agent switcher in chat window — click to connect to any department head.
Each agent: own persona, own Piper voice, own MD config file, own model.

**S5 — Knowledge Ingestor (Drag & Drop)**
Drop zone in HUD for files and URLs.
Content extracted → AI chunks into 400-500 line segments → chapter files in Obsidian.
Master index per topic. Knowledge search endpoint for agents.
New skill: knowledge_ingestor. New endpoints: /ingest/file, /ingest/url, /knowledge/search

---

### 🟡 PHASE 2 — AGENT ARCHITECTURE (Sessions 6–9)

**S6 — CEO Orchestrator + 8 Department Heads**
One department head per Elite Nexus AI service (see list above).
LangGraph supervisor routes tasks by service type and complexity.
Each head has up to 10 sub-agent slots.
Sub-agents use local vLLM (free) for execution.
CEO only escalates to Claude Sonnet for complex tool-use or client-facing work.
All department heads have their MD persona file and vault assignment.

**S7 — CFO Agent + Factory Management**
CFO oversees all 5 income factories + financial reporting.
Sub-agents: trend researcher, factory monitors (alpha + beta), revenue tracker, pricing optimizer.
Competitive KPI leaderboard in HUD (Alpha vs Beta).
Trend scraper feeds factory pipeline automatically.

**S8 — Vault Assignment System**
Per-agent vault configuration panel.
Three vault types per agent: Daily Notes, Projects, Knowledge Base.
Auto-chunking: 500-line max, splits into topic chapters.
Knowledge vault pre-loaded as context before task execution.
Agent expertise grows automatically over time.

**S9 — Wake Word + Global Hotkey**
Whisper-based "Hermes" / "Matrix" wake word.
Ctrl+Space system-wide hotkey.
Auto-captures clipboard + active window on summon.
Context fed to active department head automatically.

---

### 🟠 PHASE 3 — 5-FACTORY PRODUCTION ENGINE (Sessions 10–14)

**S10 — Factory Infrastructure**
/mnt/data/ai_factory/ directory structure.
core_orchestrator.sh, factory_state.db, trend_scraper.py, image_upscaler.py.
VRAM throttle mapping. Draft enforcement (never auto-publish).

**S11 — Factory 1: Identity POD Store**
Gothic/Techwear/Cyberpunk/Y2K niche.
SDXL → Real-ESRGAN 300 DPI → Printify/Printful API (drafts only).

**S11 — Factory 2: Stream Asset Factory**
Twitch/YouTube/Kick streamers.
SDXL + Stable Video Diffusion → Gumroad + Etsy (drafts).

**S12 — Factory 3: Gothic Digital Press**
Dark academia, journaling.
PDF planner generation → Etsy + Gumroad (drafts).

**S12 — Factory 4: Developer Utility Lab**
Tech workers, devs.
Notion workspaces, LLM prompt workbooks → Gumroad (drafts).

**S13 — Factory 5: Vector Crafting House**
Cricut crafters, laser cutters.
potrace → ImageMagick SVG → Creative Market + Etsy (drafts).

**S14 — Marketplace API Integration**
Printify, Gumroad, Etsy, Creative Market.
A/B testing engine. Account health monitor. Revenue dashboard in HUD.
CFO Agent monitors all factory outputs and revenue.

---

### 🔵 PHASE 4 — CONTEXT ENGINE (Sessions 15–17)

**S15 — Neural Brain Vault Visualization**
(From @jonathon.mj TikTok — concept only, not built yet)
Obsidian vault rendered as living brain particle visualization.
Brain regions = knowledge clusters. Firing rate = recent activity.
Toggle: Brain View ↔ Graph View.
"Feed the brain" input lights up relevant regions.

**S16 — Nexus Codebase Graph**
(From @buildwithneej TikTok — concept only, not built yet)
Matrix OS repo visualized as connected node graph.
Claude Code navigates before modifying.
"One Command Run" fires entire factory pipeline.
Hooks panel: PRE/POST hooks + MCP configs visible in HUD.

**S17 — Semantic Screen Awareness**
EasyOCR on active window every 30 seconds.
Context panel in HUD: active window, clipboard, relevant vault notes.
Agent sees what you're working on without being told.

---

### 🔵 PHASE 5 — SECURITY + DATABASE (Sessions 18–19)

**S18 — Iris Vault (PostgreSQL + pgvector)**
Docker container with pgvector extension.
Tables: TokenLedger, SecurityAuditLog, ProjectMemory, ChatMessages, KnowledgeChunks.
RAG search over all Obsidian vault content.
Core Blueprints: compress old projects for unlimited context.

**S19 — Zero-Trust Security Matrix**
Green (auto) / Yellow (notify) / Red (HITL approve in HUD).
Git snapshot before every Red action. Rollback button.
All actions logged to SecurityAuditLog.

---

### 🟣 PHASE 6 — LOCAL BUILDER SANDBOX (Sessions 20–21)

**S20 — n8n + Dify Docker Sandbox**
n8n (port 5678) + Dify (port 3000) self-hosted.
Hermes creates workflows and RAG pipelines via API.

**S21 — Idle Dreaming Mode**
Triggers after 15 min idle. Local vLLM only — zero cost.
Recursive Skill Synthesis. Skill Ledger in HUD.
Natural language skill creation. Dream summary in morning briefing.

---

### ⚫ PHASE 7 — PRODUCTION APP (Sessions 22–23)

**S22 — Tauri 2.0 Desktop App**
Wrap HUD in Tauri 2.0. Transparent overlay. Rust backend.
Encrypted credential vault. Resource Governor.

**S23 — Virtual Agent Office 3D**
React Three Fiber. Drag-and-drop office layout.
3D avatars for all department heads. Factory production line view.
Dynamic avatar spawning for sub-agents.

---

## 💡 WHAT EACH NEW FEATURE ENABLES

### Knowledge Ingestor (Drag & Drop)
Drop any document, URL, or text file and agents instantly become experts on that topic.
Client brief dropped → consulting agent knows the business before the call.
Competitor site dropped → marketing agent knows exactly what to position against.
Technical docs dropped → product development agent can build without guessing.
Chunks stored as readable Obsidian chapters → agents recall specific sections fast.

### Department Head Architecture (8 Heads + CFO)
Each service line has a dedicated expert agent that stays focused.
Sub-agents under each head run on free local vLLM — only the head escalates to paid models.
A website job never goes to the voice bot head — routing is precise.
Up to 10 sub-agents work in parallel under each head — 5x faster than sequential execution.
CFO Agent ties all factory income to a single financial intelligence layer.

### Vault Assignment Per Agent
Each agent writes its own daily notes in a readable, chunked format.
Knowledge accumulates — an agent that worked on 50 chatbot projects knows chatbot patterns.
When given a new task, the agent loads its relevant KB vault chunks first.
This is how agents become genuine domain experts without retraining.

---

## 🔑 SERVICES & PORTS

| Service | Port | Status |
|---------|------|--------|
| Matrix Bridge | 8765 | ✅ Running |
| vLLM Qwen2.5-72B AWQ | 8000 | ✅ On demand |
| Ollama | 11434 | ✅ Running |
| Kokoro TTS Docker | 8880 | ⚠ Stop before vLLM |
| n8n | 5678 | 🔵 Phase 6 |
| Dify | 3000 | 🔵 Phase 6 |
| Iris Vault PostgreSQL | 5432 | 🔵 Phase 5 |

---

*Elite Nexus AI — Matrix OS Master Project Guide v3*
*Updated: May 25, 2026 · Next: Session 1 — Financial Telemetry Footer*
