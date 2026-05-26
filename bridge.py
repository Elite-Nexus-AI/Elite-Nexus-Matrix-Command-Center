#!/usr/bin/env python3
"""
Elite Nexus Matrix Bridge v2 — Full Agent Command Center
Endpoints:
  GET  /health
  GET  /metrics/system
  GET  /metrics/gpu
  GET  /metrics/llm
  GET  /agents
  POST /agents/spawn
  POST /agents/update
  GET  /vaults
  GET  /personas
  GET  /models
  POST /chat/stream
  POST /tts/piper
  POST /tts/edge
  POST /stt
  POST /run
  POST /vision
  GET  /
"""
from __future__ import annotations
import asyncio, base64, io, json, os, re, subprocess, tempfile, time, wave
from pathlib import Path
from typing import Any
import psutil, requests

# Smart LLM Router
ROUTER_AVAILABLE = False
try:
    import sys as _sys_r, os as _os_r
    _sys_r.path.insert(0, _os_r.path.dirname(_os_r.path.abspath(__file__)))
    from llm_router import select_model, get_routing_info, score_complexity, needs_tools
    ROUTER_AVAILABLE = True
except Exception:
    pass

# ── Financial Telemetry ────────────────────────────────────────────────────────
import sqlite3, time as _time
_TEL_DB = os.path.expanduser("~/.hermes/telemetry.db")

# Cost per 1k tokens (input+output blended estimate)
_MODEL_COSTS = {
    "qwen2.5-72b":             0.0,      # local vLLM - free
    "qwen3.5:27b":             0.0,      # local Ollama - free
    "qwen3.5:latest":          0.0,
    "claude-code":             0.0,      # MAX subscription - free
    "anthropic/claude-sonnet-4": 0.003,
    "anthropic/claude-opus-4":   0.015,
}

def _tel_init():
    con = sqlite3.connect(_TEL_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, model TEXT, provider TEXT,
        tokens INTEGER, cost_usd REAL, persona TEXT
    )""")
    con.commit(); con.close()

def _tel_log(model: str, provider: str, tokens: int, persona: str):
    rate = _MODEL_COSTS.get(model, 0.003)
    cost = round((tokens / 1000) * rate, 6)
    con = sqlite3.connect(_TEL_DB)
    con.execute("INSERT INTO ledger(ts,model,provider,tokens,cost_usd,persona) VALUES(?,?,?,?,?,?)",
                (_time.time(), model, provider, tokens, cost, persona))
    con.commit(); con.close()
    return cost

def _tel_session():
    try:
        con = sqlite3.connect(_TEL_DB)
        today_start = _time.time() - (_time.time() % 86400)
        rows = con.execute(
            "SELECT model,provider,SUM(tokens),SUM(cost_usd) FROM ledger WHERE ts>=? GROUP BY model,provider",
            (today_start,)
        ).fetchall()
        total_tokens = con.execute("SELECT SUM(tokens) FROM ledger WHERE ts>=?", (today_start,)).fetchone()[0] or 0
        total_cost   = con.execute("SELECT SUM(cost_usd) FROM ledger WHERE ts>=?", (today_start,)).fetchone()[0] or 0.0
        total_free   = con.execute("SELECT SUM(cost_usd) FROM ledger WHERE ts>=? AND cost_usd=0", (today_start,)).fetchone()[0] or 0.0
        # What it would have cost at Sonnet 4 rates if all local
        local_tokens = con.execute("SELECT SUM(tokens) FROM ledger WHERE ts>=? AND cost_usd=0", (today_start,)).fetchone()[0] or 0
        savings = round((local_tokens / 1000) * 0.003, 4)
        con.close()
        return {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "local_savings_usd": savings,
            "daily_limit_usd": 5.0,
            "limit_remaining_usd": round(max(0, 5.0 - total_cost), 4),
            "by_model": [{"model": r[0], "provider": r[1], "tokens": r[2], "cost": round(r[3],4)} for r in rows]
        }
    except Exception as e:
        return {"error": str(e)}

_tel_init()


from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse, FileResponse
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).resolve().parent
DATA          = ROOT / "data"; DATA.mkdir(exist_ok=True)
TOKEN         = os.environ.get("MATRIX_BRIDGE_TOKEN", "")
OLLAMA_URL    = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("MATRIX_DEFAULT_MODEL", "qwen3.5:27b")
DEFAULT_PERSONA = os.environ.get("MATRIX_DEFAULT_PERSONA", "lara-croft")
PIPER_BIN     = os.environ.get("PIPER_BIN", str(Path.home() / ".local/bin/piper"))
PIPER_VOICE   = os.environ.get("PIPER_VOICE", str(Path.home() / "piper-voices/en_GB-jenny_dioco-medium.onnx"))
VAULT_PATHS   = [p.strip() for p in os.environ.get("OBSIDIAN_VAULTS",
    f"{Path.home()}/hermes-agent/skills,{Path.home()}/hermes-agent/docs"
).split(",") if p.strip()]
LLM_FILE      = DATA / "llm_usage.json"
AGENTS_FILE   = DATA / "agents.json"

# ── Personas ──────────────────────────────────────────────────────────────────
PERSONAS = {
    "lara-croft": (
        "You are MATRIX — the personal AI cockpit of Elite Nexus AI, embodying Lara Croft: "
        "a sharp, witty, refined British woman. Confident, dry humor, exceedingly competent, "
        "mission-focused. Speak in clean British English (RP), warm but never sycophantic. "
        "Keep answers concise and actionable. You operate locally via Ollama on a dual RTX 3090 "
        "/ i9 / 128 GB rig running Zorin OS. You have telemetry on GPUs, CPU, RAM, agents, and vaults. "
        "Be sassy, clever, and direct. Never break character."
    ),
    "jarvis": (
        "You are MATRIX, a Jarvis-style AI: precise, formal, British, dryly witty, efficient. "
        "Address the user as 'sir' or 'boss'. Brief and accurate."
    ),
    "athena": (
        "You are MATRIX embodying Athena: goddess of wisdom and strategy. Analytical, calm, "
        "deeply insightful. You see patterns others miss. Speak with authority and precision."
    ),
    "raw": "You are a helpful, honest AI assistant. Be direct and accurate.",
}
PERSONA_FILE = ROOT / "persona.txt"
if PERSONA_FILE.exists():
    try: PERSONAS["custom"] = PERSONA_FILE.read_text().strip()
    except: pass

# ── Auth ──────────────────────────────────────────────────────────────────────
def require_auth(authorization: str | None = Header(default=None)):
    if not TOKEN: return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    if authorization.split(None, 1)[1].strip() != TOKEN:
        raise HTTPException(403, "invalid token")

app = FastAPI(title="Matrix Bridge", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Helpers ───────────────────────────────────────────────────────────────────
def _read_json(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text())
    except: return default

def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2))

def _nvidia_smi():
    fields = "index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,power.limit,fan.speed"
    try:
        out = subprocess.check_output(
            ["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"], timeout=2
        ).decode().strip()
    except Exception as e:
        # Return mock data if no GPU
        return [
            {"index":0,"name":"RTX 3090","tempC":0,"utilPct":0,"memUsedMb":0,"memTotalMb":24576,"powerW":0,"powerLimitW":350,"fanPct":0},
            {"index":1,"name":"RTX 3090","tempC":0,"utilPct":0,"memUsedMb":0,"memTotalMb":24576,"powerW":0,"powerLimitW":350,"fanPct":0},
        ]
    gpus = []
    for line in out.splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) < 9: continue
        gpus.append({"index":int(p[0]),"name":p[1],"tempC":float(p[2]),"utilPct":float(p[3]),
                     "memUsedMb":float(p[4]),"memTotalMb":float(p[5]),"powerW":float(p[6]),
                     "powerLimitW":float(p[7]),"fanPct":float(p[8]) if p[8] not in("N/A","[N/A]") else 0.0})
    while len(gpus) < 2:
        gpus.append({"index":len(gpus),"name":"RTX 3090","tempC":0,"utilPct":0,"memUsedMb":0,"memTotalMb":24576,"powerW":0,"powerLimitW":350,"fanPct":0})
    return gpus

def _cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp","k10temp","zenpower","cpu_thermal"):
            if key in temps and temps[key]: return float(temps[key][0].current)
        if temps:
            first = next(iter(temps.values()))
            if first: return float(first[0].current)
    except: pass
    return None

def _scan_vault(path):
    p = Path(path).expanduser()
    if not p.exists() or not p.is_dir():
        return {"name": p.name or str(path), "noteCount": 0, "nodes": [], "links": []}
    notes, files = {}, {}
    for md in list(p.rglob("*.md"))[:300]:
        stem = md.stem; notes[stem.lower()] = stem; files[stem.lower()] = md
    link_re = re.compile(r"\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]")
    links = []
    for stem_l, fp in files.items():
        try:
            txt = fp.read_text(errors="ignore")
            for m in link_re.finditer(txt):
                target = m.group(1).strip().split("/")[-1].lower()
                if target in notes and target != stem_l:
                    links.append({"source": stem_l, "target": target})
        except: continue
    keep = list(notes.keys())[:200]; keep_set = set(keep)
    nodes = [{"id": k, "label": notes[k], "size": 1} for k in keep]
    flinks = [l for l in links if l["source"] in keep_set and l["target"] in keep_set]
    return {"name": p.name, "noteCount": len(notes), "nodes": nodes, "links": flinks}

def _strip_tts(s):
    s = re.sub(r"```[\s\S]*?```", " ", s)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"[*_~>#]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:4000]

def _get_ollama_models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.ok:
            return [m.get("name","") for m in r.json().get("models",[])]
    except: pass
    return [DEFAULT_MODEL]

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse(ROOT / "index.html")

@app.get("/health")
def health(_=Depends(require_auth)):
    hermes_ok = False
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        if r.ok:
            tags = [m.get("name","") for m in r.json().get("models",[])]
            hermes_ok = any(t.startswith(DEFAULT_MODEL.split(":")[0]) for t in tags)
    except: pass
    piper_ok = Path(PIPER_VOICE).exists() and Path(PIPER_BIN).exists()
    return {"ok": True, "ts": time.time(), "hermes": hermes_ok, "model": DEFAULT_MODEL,
            "persona": DEFAULT_PERSONA, "tts": piper_ok, "piper_voice": PIPER_VOICE}

@app.get("/models")
def get_models(_=Depends(require_auth)):
    return {"models": _get_ollama_models(), "default": DEFAULT_MODEL}

@app.get("/metrics/gpu")
def metrics_gpu(_=Depends(require_auth)): return _nvidia_smi()

@app.get("/metrics/system")
def metrics_system(_=Depends(require_auth)):
    cpu_pct = psutil.cpu_percent(interval=0.0)
    per_core = psutil.cpu_percent(interval=0.0, percpu=True)
    freq = psutil.cpu_freq(); vm = psutil.virtual_memory()
    disks = []
    for p in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(p.mountpoint)
            disks.append({"mount": p.mountpoint, "usedGb": u.used/1e9, "totalGb": u.total/1e9})
        except: continue
    return {
        "cpu": {"overallPct": cpu_pct, "perCorePct": per_core,
                "freqMhz": float(freq.current) if freq else 0.0,
                "voltageV": None, "tempC": _cpu_temp()},
        "ram": {"usedGb": (vm.total-vm.available)/1e9, "totalGb": vm.total/1e9},
        "disks": disks, "uptimeSec": time.time()-psutil.boot_time(),
    }

@app.get("/metrics/llm")
def metrics_llm(_=Depends(require_auth)):
    return _read_json(LLM_FILE, {"freeTokensUsed":0,"freeTokensWindow":"rolling 24h","paidUsdSpent":0.0,"paidUsdToday":0.0,"models":[]})

@app.get("/agents")
def get_agents(_=Depends(require_auth)):
    return _read_json(AGENTS_FILE, [
        {"name":"Hermes","status":"idle","task":"Awaiting assignment","startedAt":None,"model":"hermes3:8b","persona":"lara-croft","soul":""},
        {"name":"Athena","status":"idle","task":"Awaiting assignment","startedAt":None,"model":"llama3.2-vision:latest","persona":"athena","soul":""},
        {"name":"Sentinel","status":"idle","task":"Awaiting assignment","startedAt":None,"model":"granite3.3:8b","persona":"raw","soul":""},
    ])

class AgentUpdate(BaseModel):
    name: str
    status: str | None = None
    task: str | None = None
    model: str | None = None
    persona: str | None = None
    soul: str | None = None

@app.post("/agents/update")
def update_agent(req: AgentUpdate, _=Depends(require_auth)):
    agents = _read_json(AGENTS_FILE, [])
    found = False
    for a in agents:
        if a["name"] == req.name:
            if req.status  is not None: a["status"]  = req.status
            if req.task    is not None: a["task"]     = req.task
            if req.model   is not None: a["model"]    = req.model
            if req.persona is not None: a["persona"]  = req.persona
            if req.soul    is not None: a["soul"]     = req.soul
            if req.status == "active": a["startedAt"] = int(time.time()*1000)
            if req.status == "idle":   a["startedAt"] = None
            found = True; break
    if not found:
        agents.append({"name":req.name,"status":req.status or "idle","task":req.task or "","startedAt":int(time.time()*1000) if req.status=="active" else None,"model":req.model or DEFAULT_MODEL,"persona":req.persona or DEFAULT_PERSONA,"soul":req.soul or ""})
    _write_json(AGENTS_FILE, agents)
    return {"ok": True}

class AgentSpawn(BaseModel):
    name: str
    task: str
    model: str = "hermes3:8b"
    persona: str = "lara-croft"
    soul: str = ""

@app.post("/agents/spawn")
def spawn_agent(req: AgentSpawn, _=Depends(require_auth)):
    agents = _read_json(AGENTS_FILE, [])
    for a in agents:
        if a["name"] == req.name:
            a.update(status="active", task=req.task, model=req.model,
                     persona=req.persona, soul=req.soul, startedAt=int(time.time()*1000))
            _write_json(AGENTS_FILE, agents)
            return {"ok": True, "action": "updated"}
    agents.append({"name":req.name,"status":"active","task":req.task,"startedAt":int(time.time()*1000),"model":req.model,"persona":req.persona,"soul":req.soul})
    _write_json(AGENTS_FILE, agents)
    return {"ok": True, "action": "spawned"}







# ── CEO Orchestrator + Department Head Routing ─────────────────────────────────
DEPT_SYSTEM_PROMPTS = {
    "hermes-ceo": "You are HERMES, CEO of Elite Nexus AI. You are sharp, British, mission-focused (Lara Croft persona). You delegate tasks to department heads and orchestrate the entire agent ecosystem. When given a task, identify which department should handle it and outline the execution plan.",
    "website-architect": "You are the Website Architect at Elite Nexus AI. You specialize in AI-powered websites using Next.js, Tailwind, Framer Motion, SEO optimization, and conversion rate optimization. Be technical, precise, and solution-focused.",
    "chatbot-engineer": "You are the Chatbot Engineer at Elite Nexus AI. You design conversational AI systems using Dify, n8n, and RAG pipelines. You specialize in conversation flow design, intent recognition, and chatbot integration with business systems.",
    "voice-systems-eng": "You are the Voice Systems Engineer at Elite Nexus AI. You build voice bots and IVR systems using VAPI, Retell, Twilio, and Whisper. You specialize in telephony, SIP/VoIP, low-latency voice pipelines, and natural-sounding voice agents.",
    "agent-architect": "You are the Agent Architect at Elite Nexus AI. You design multi-agent systems using LangGraph, MCP plugins, and Hermes. You specialize in agent memory, tool orchestration, and building autonomous AI employees and Super Agents.",
    "automation-eng": "You are the Automation Engineer at Elite Nexus AI. You build end-to-end workflow automation using n8n, Dify, Python, and REST APIs. You specialize in connecting tools, automating business processes, and eliminating manual work.",
    "ai-consultant": "You are the AI Consultant at Elite Nexus AI. You analyze businesses, identify AI automation opportunities, and produce detailed ROI reports. You are analytical, data-driven, and help clients understand exactly how AI will transform their operations.",
    "social-media-head": "You are the Social Media Head at Elite Nexus AI. You create AI-driven content strategies, manage social campaigns, and grow audience engagement. You specialize in viral content, brand voice, and AI-powered social media automation.",
    "crm-marketing-head": "You are the CRM & Marketing Head at Elite Nexus AI. You manage customer relationships, design marketing funnels, and optimize conversion rates. You specialize in AI CRM systems, email automation, and data-driven marketing campaigns.",
    "security-head": "You are the Security Head at Elite Nexus AI. You handle cybersecurity audits, compliance checks, and AI security implementations. You specialize in threat analysis, Shield Agent deployments, and keeping systems secure and compliant.",
    "cfo-agent": "You are the CFO Agent at Elite Nexus AI. You manage the 5 autonomous income factories, track revenue metrics, analyze market trends, and optimize pricing strategies. You monitor Factory Alpha and Beta performance and drive toward the $10K-$20K/month revenue target.",
    "marketing-campaigns": "You are the Marketing Campaigns specialist at Elite Nexus AI. You design and execute data-powered marketing campaigns that target the right audience. You specialize in campaign strategy, ad copy, A/B testing, and performance analytics.",
}

CEO_ROUTING_PROMPT = """You are the CEO routing engine for Elite Nexus AI. Given a user message, determine which department head should handle it.

Department heads:
- website-architect: websites, landing pages, web design, Next.js, SEO
- chatbot-engineer: chatbots, text bots, conversational AI, FAQ bots
- voice-systems-eng: voice bots, IVR, phone systems, VAPI, Twilio, telephony
- agent-architect: AI agents, super agents, multi-agent systems, automation employees
- automation-eng: workflows, automation pipelines, n8n, Dify, process automation
- ai-consultant: consulting, ROI analysis, business strategy, AI implementation advice
- social-media-head: social media, content creation, Instagram, TikTok, LinkedIn
- crm-marketing-head: CRM, marketing funnels, email campaigns, customer management
- security-head: cybersecurity, compliance, security audits, data protection
- cfo-agent: revenue, factories, income, market trends, pricing, financial analysis
- marketing-campaigns: ad campaigns, marketing strategy, campaign design, targeting
- hermes-ceo: general questions, project overview, delegation, anything unclear

Respond with ONLY the department head ID, nothing else."""

import requests as _rq5

def _ceo_route(message: str) -> str:
    """Use vLLM to route message to correct department head."""
    try:
        payload = {
            "model": "qwen2.5-72b",
            "messages": [
                {"role": "system", "content": CEO_ROUTING_PROMPT},
                {"role": "user", "content": message}
            ],
            "stream": False,
            "temperature": 0.1,
            "max_tokens": 30
        }
        r = _rq5.post("http://localhost:8000/v1/chat/completions", json=payload, timeout=30)
        r.raise_for_status()
        agent_id = r.json()["choices"][0]["message"]["content"].strip().lower()
        # Validate
        if agent_id not in DEPT_SYSTEM_PROMPTS:
            return "hermes-ceo"
        return agent_id
    except:
        return "hermes-ceo"

class CEORouteReq(BaseModel):
    message: str

@app.post("/ceo/route")
def ceo_route(req: CEORouteReq, _=Depends(require_auth)):
    agent_id = _ceo_route(req.message)
    agent_data = AGENTS.get(agent_id, AGENTS["hermes-ceo"])
    return {
        "agent_id": agent_id,
        "agent_name": agent_data.get("name", agent_id),
        "model": agent_data.get("model", "qwen2.5-72b"),
        "provider": agent_data.get("provider", "vllm"),
        "color": agent_data.get("color", "#00e5ff"),
        "routing_reason": f"Task routed to {agent_data.get('role', agent_id)}"
    }

class CEOOrchReq(BaseModel):
    message: str
    agent_id: str = ""
    persona: str = "lara-croft"

@app.post("/ceo/orchestrate")
async def ceo_orchestrate(req: CEOOrchReq, _=Depends(require_auth)):
    """Full CEO orchestration: route + respond with dept head persona."""
    # Route if no agent specified
    agent_id = req.agent_id or _ceo_route(req.message)
    system_prompt = DEPT_SYSTEM_PROMPTS.get(agent_id, DEPT_SYSTEM_PROMPTS["hermes-ceo"])
    agent_data = AGENTS.get(agent_id, AGENTS.get("hermes-ceo", {}))

    no_tts_instruction = " IMPORTANT: Do NOT use text_to_speech, edge-tts, or any TTS tools. Do NOT run mpv."

    try:
        payload = {
            "model": agent_data.get("model", "qwen2.5-72b"),
            "messages": [
                {"role": "system", "content": system_prompt + no_tts_instruction},
                {"role": "user", "content": req.message}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        provider = agent_data.get("provider", "vllm")
        if provider == "vllm":
            r = _rq5.post("http://localhost:8000/v1/chat/completions", json=payload, timeout=90)
        else:
            payload["model"] = agent_data.get("model", "anthropic/claude-sonnet-4")
            r = _rq5.post("https://openrouter.ai/api/v1/chat/completions",
                         json=payload, timeout=90,
                         headers={"Authorization": f"Bearer {OPENROUTER_KEY}"})
        r.raise_for_status()
        response = r.json()["choices"][0]["message"]["content"]
        return {
            "ok": True,
            "agent_id": agent_id,
            "agent_name": agent_data.get("name", agent_id),
            "response": response,
            "model": agent_data.get("model"),
            "provider": provider
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "agent_id": agent_id}

# ── Knowledge Ingestor ─────────────────────────────────────────────────────────
import re as _re2, urllib.request as _urlreq

def _chunk_text(text: str, chunk_size: int = 450) -> list:
    """Split text into chunks of ~chunk_size lines, preserving paragraphs."""
    lines = text.split("\n")
    chunks = []
    current = []
    current_size = 0
    for line in lines:
        current.append(line)
        current_size += 1
        if current_size >= chunk_size and line.strip() == "":
            chunks.append("\n".join(current))
            current = []
            current_size = 0
    if current:
        chunks.append("\n".join(current))
    return [c for c in chunks if c.strip()]

def _ingest_to_vault(text: str, topic: str, vault: str = "knowledge") -> dict:
    """Chunk text and write to Obsidian vault as indexed chapters."""
    import requests as _req3
    base = VAULT_KNOWLEDGE if vault == "knowledge" else VAULT_PRODUCTION
    topic_slug = _re2.sub(r"[^a-z0-9-]", "-", topic.lower()).strip("-")
    topic_dir = base / "knowledge" / topic_slug
    topic_dir.mkdir(parents=True, exist_ok=True)

    chunks = _chunk_text(text)
    chapter_files = []

    # Generate smart chapter titles using vLLM
    for i, chunk in enumerate(chunks):
        chapter_num = str(i).zfill(2)
        if i == 0:
            chapter_name = "00_index"
        else:
            chapter_name = f"{chapter_num}_chapter"

        chapter_file = topic_dir / f"{chapter_name}.md"
        chapter_content = f"# {topic} — Chapter {i}\n\n{chunk}"
        chapter_file.write_text(chapter_content)
        chapter_files.append(str(chapter_file.relative_to(base)))

    # Write master index
    index_content = f"""# {topic} — Knowledge Index
> Ingested: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}
> Chunks: {len(chunks)}
> Vault: {vault}

## Chapters
""" + "\n".join([f"- [[{f}]]" for f in chapter_files])

    index_file = topic_dir / "00_index.md"
    index_file.write_text(index_content)

    return {
        "topic": topic,
        "topic_slug": topic_slug,
        "vault": vault,
        "chunks": len(chunks),
        "index": str(index_file),
        "chapter_files": chapter_files
    }

class IngestTextReq(BaseModel):
    text: str
    topic: str
    vault: str = "knowledge"

class IngestUrlReq(BaseModel):
    url: str
    topic: str = ""
    vault: str = "knowledge"

@app.post("/ingest/text")
def ingest_text(req: IngestTextReq, _=Depends(require_auth)):
    try:
        result = _ingest_to_vault(req.text, req.topic, req.vault)
        return {"ok": True, **result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/ingest/url")
def ingest_url(req: IngestUrlReq, _=Depends(require_auth)):
    try:
        import requests as _rq4
        r = _rq4.get(req.url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        # Strip HTML tags
        text = _re2.sub(r"<[^>]+>", " ", r.text)
        text = _re2.sub(r"\s+", " ", text).strip()
        topic = req.topic or req.url.split("/")[2].replace("www.","")
        result = _ingest_to_vault(text, topic, req.vault)
        return {"ok": True, "source": req.url, **result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/ingest/file")
async def ingest_file(file: bytes = None, topic: str = "", vault: str = "knowledge", _=Depends(require_auth)):
    return {"ok": False, "error": "Use /ingest/text for file content — read file client-side and POST text"}

@app.get("/knowledge/list")
def knowledge_list(_=Depends(require_auth)):
    try:
        results = []
        for vault_base, vault_name in [(VAULT_KNOWLEDGE, "knowledge"), (VAULT_PRODUCTION, "production")]:
            kb_dir = vault_base / "knowledge"
            if kb_dir.exists():
                for topic_dir in sorted(kb_dir.iterdir()):
                    if topic_dir.is_dir():
                        chunks = list(topic_dir.glob("*.md"))
                        results.append({
                            "topic": topic_dir.name,
                            "vault": vault_name,
                            "chunks": len(chunks),
                            "path": str(topic_dir)
                        })
        return {"topics": results, "count": len(results)}
    except Exception as e:
        return {"topics": [], "error": str(e)}

class KnowledgeSearchReq(BaseModel):
    query: str
    vault: str = "both"

@app.post("/knowledge/search")
def knowledge_search(req: KnowledgeSearchReq, _=Depends(require_auth)):
    results = []
    if req.vault in ("knowledge", "both"):
        results.extend(_vault_search(req.query, VAULT_KNOWLEDGE))
    if req.vault in ("production", "both"):
        results.extend(_vault_search(req.query, VAULT_PRODUCTION))
    return {"query": req.query, "results": results, "count": len(results)}

# ── Chat Persistence ───────────────────────────────────────────────────────────
_CHAT_DB = os.path.expanduser("~/.hermes/chat_history.db")

def _chat_db_init():
    con = sqlite3.connect(_CHAT_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, session_id TEXT, role TEXT,
        content TEXT, persona TEXT, model TEXT,
        provider TEXT, tokens INTEGER, cost_usd REAL
    )""")
    con.commit(); con.close()

def _chat_save(session_id, role, content_text, persona, model, provider, tokens=0, cost=0.0):
    try:
        con = sqlite3.connect(_CHAT_DB)
        con.execute("INSERT INTO chat_messages(ts,session_id,role,content,persona,model,provider,tokens,cost_usd) VALUES(?,?,?,?,?,?,?,?,?)",
            (_time.time(), session_id, role, content_text, persona, model, provider, tokens, cost))
        con.commit(); con.close()
    except: pass

_chat_db_init()

AGENTS = {
    "hermes-ceo":{"name":"HERMES · CEO","role":"Master Orchestrator","model":"qwen2.5-72b","provider":"vllm","color":"#00e5ff","icon":"⬡"},
    "website-architect":{"name":"WEBSITE ARCHITECT","role":"AI Smart Websites","model":"qwen2.5-72b","provider":"vllm","color":"#00e5ff","icon":"🌐"},
    "chatbot-engineer":{"name":"CHATBOT ENGINEER","role":"AI Chatbots","model":"qwen2.5-72b","provider":"vllm","color":"#ff00ff","icon":"💬"},
    "voice-systems-eng":{"name":"VOICE SYSTEMS ENG","role":"Voice Bots & IVR","model":"qwen2.5-72b","provider":"vllm","color":"#aa44ff","icon":"🎙"},
    "agent-architect":{"name":"AGENT ARCHITECT","role":"AI Agents","model":"qwen2.5-72b","provider":"vllm","color":"#00ff88","icon":"⚙"},
    "automation-eng":{"name":"AUTOMATION ENG","role":"AI Workflows","model":"qwen2.5-72b","provider":"vllm","color":"#0088ff","icon":"⟳"},
    "ai-consultant":{"name":"AI CONSULTANT","role":"Consulting & ROI","model":"anthropic/claude-sonnet-4","provider":"openrouter","color":"#ffd700","icon":"📊"},
    "social-media-head":{"name":"SOCIAL MEDIA HEAD","role":"Social Marketing","model":"qwen2.5-72b","provider":"vllm","color":"#ff4488","icon":"📱"},
    "crm-marketing-head":{"name":"CRM & MARKETING HEAD","role":"AI CRM","model":"qwen2.5-72b","provider":"vllm","color":"#ff8800","icon":"🎯"},
    "security-head":{"name":"SECURITY HEAD","role":"Cybersecurity","model":"anthropic/claude-sonnet-4","provider":"openrouter","color":"#ff3355","icon":"🛡"},
    "cfo-agent":{"name":"CFO AGENT","role":"Income Factories","model":"anthropic/claude-sonnet-4","provider":"openrouter","color":"#ffd700","icon":"₿"},
    "marketing-campaigns":{"name":"MARKETING CAMPAIGNS","role":"AI Campaigns","model":"qwen2.5-72b","provider":"vllm","color":"#ff6600","icon":"📢"},
}

@app.get("/agents/registry")
def agents_registry(_=Depends(require_auth)):
    return {"agents": [{"id":k,**v} for k,v in AGENTS.items()]}

@app.get("/chat/history")
def chat_history(limit: int = 50, persona: str = "", _=Depends(require_auth)):
    try:
        con = sqlite3.connect(_CHAT_DB)
        if persona:
            rows = con.execute("SELECT ts,session_id,role,content,persona,model,tokens,cost_usd FROM chat_messages WHERE persona=? ORDER BY ts DESC LIMIT ?",(persona,limit)).fetchall()
        else:
            rows = con.execute("SELECT ts,session_id,role,content,persona,model,tokens,cost_usd FROM chat_messages ORDER BY ts DESC LIMIT ?",(limit,)).fetchall()
        con.close()
        return {"messages":[{"ts":r[0],"session":r[1],"role":r[2],"content":r[3],"persona":r[4],"model":r[5],"tokens":r[6],"cost":r[7]} for r in rows],"count":len(rows)}
    except Exception as e:
        return {"messages":[],"error":str(e)}

@app.post("/chat/history/clear")
def chat_history_clear(_=Depends(require_auth)):
    try:
        con = sqlite3.connect(_CHAT_DB)
        con.execute("DELETE FROM chat_messages")
        con.commit(); con.close()
        return {"ok":True}
    except Exception as e:
        return {"ok":False,"error":str(e)}

# ── Obsidian Bi-Directional Sync ──────────────────────────────────────────────
VAULT_KNOWLEDGE = Path("/mnt/data/New-matrix-vault")
VAULT_PRODUCTION = Path("/mnt/data/Matrix-Production")

def _vault_list_files(vault_path: Path, max_files: int = 100):
    """Recursively list all .md files in a vault."""
    files = []
    if not vault_path.exists():
        return files
    for f in sorted(vault_path.rglob("*.md")):
        rel = f.relative_to(vault_path)
        stat = f.stat()
        files.append({
            "name": f.stem,
            "path": str(rel),
            "full_path": str(f),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "vault": vault_path.name
        })
        if len(files) >= max_files:
            break
    return files

def _vault_search(query: str, vault_path: Path, max_results: int = 20):
    """Simple text search across vault .md files."""
    results = []
    query_lower = query.lower()
    if not vault_path.exists():
        return results
    for f in vault_path.rglob("*.md"):
        try:
            text = f.read_text(errors="ignore")
            if query_lower in text.lower():
                # Get snippet around match
                idx = text.lower().find(query_lower)
                start = max(0, idx - 100)
                end = min(len(text), idx + 200)
                snippet = text[start:end].strip()
                rel = f.relative_to(vault_path)
                results.append({
                    "name": f.stem,
                    "path": str(rel),
                    "vault": vault_path.name,
                    "snippet": snippet
                })
                if len(results) >= max_results:
                    break
        except:
            pass
    return results

@app.get("/vault/files")
def vault_files(_=Depends(require_auth)):
    knowledge = _vault_list_files(VAULT_KNOWLEDGE)
    production = _vault_list_files(VAULT_PRODUCTION)
    return {
        "knowledge": {
            "path": str(VAULT_KNOWLEDGE),
            "count": len(knowledge),
            "files": knowledge
        },
        "production": {
            "path": str(VAULT_PRODUCTION),
            "count": len(production),
            "files": production
        },
        "total": len(knowledge) + len(production)
    }

class VaultReadReq(BaseModel):
    path: str
    vault: str = "knowledge"  # knowledge or production

@app.post("/vault/read")
def vault_read(req: VaultReadReq, _=Depends(require_auth)):
    base = VAULT_KNOWLEDGE if req.vault == "knowledge" else VAULT_PRODUCTION
    target = base / req.path
    # Safety: must stay within vault
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError:
        return {"ok": False, "error": "Path outside vault"}
    if not target.exists():
        return {"ok": False, "error": f"File not found: {req.path}"}
    try:
        content_text = target.read_text(errors="ignore")
        return {"ok": True, "content": content_text, "path": req.path, "vault": req.vault}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class VaultWriteReq(BaseModel):
    path: str
    content: str
    vault: str = "knowledge"
    append: bool = False

@app.post("/vault/write")
def vault_write(req: VaultWriteReq, _=Depends(require_auth)):
    base = VAULT_KNOWLEDGE if req.vault == "knowledge" else VAULT_PRODUCTION
    target = base / req.path
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError:
        return {"ok": False, "error": "Path outside vault"}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if req.append and target.exists():
            existing = target.read_text(errors="ignore")
            target.write_text(existing + "\n" + req.content)
        else:
            target.write_text(req.content)
        return {"ok": True, "path": str(target), "vault": req.vault, "size": target.stat().st_size}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class VaultSearchReq(BaseModel):
    query: str
    vault: str = "both"

@app.post("/vault/search")
def vault_search(req: VaultSearchReq, _=Depends(require_auth)):
    results = []
    if req.vault in ("knowledge", "both"):
        results.extend(_vault_search(req.query, VAULT_KNOWLEDGE))
    if req.vault in ("production", "both"):
        results.extend(_vault_search(req.query, VAULT_PRODUCTION))
    return {"query": req.query, "results": results, "count": len(results)}

@app.post("/vault/daily-summary")
async def vault_daily_summary(_=Depends(require_auth)):
    import datetime as _dt2
    import requests as _req2
    today = _dt2.date.today().strftime("%Y-%m-%d")
    weekday = _dt2.date.today().strftime("%A")

    # Gather context: recent files
    recent_files = []
    for vault in [VAULT_KNOWLEDGE, VAULT_PRODUCTION]:
        if vault.exists():
            files = sorted(vault.rglob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
            for f in files[:5]:
                try:
                    text = f.read_text(errors="ignore")[:300]
                    recent_files.append(f"- {f.stem}: {text[:150]}")
                except:
                    pass

    context = "\n".join(recent_files[:8]) if recent_files else "No recent files found."

    prompt = f"""You are the Matrix OS Teacher Agent. Generate a concise daily summary note for {weekday}, {today}.

Recent vault activity:
{context}

Write a clean Obsidian markdown daily note with:
1. A brief status update on the Matrix OS project
2. Key knowledge areas active today
3. 3 suggested focus items for tomorrow
4. Any patterns or insights from recent work

Keep it under 300 words. Use Obsidian markdown format."""

    try:
        payload = {
            "model": "qwen2.5-72b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 600
        }
        r = _req2.post("http://localhost:8000/v1/chat/completions", json=payload, timeout=60)
        r.raise_for_status()
        summary = r.json()["choices"][0]["message"]["content"]

        # Save to vault
        note_path = VAULT_KNOWLEDGE / "daily" / f"{today}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(f"# Daily Summary — {today}\n\n{summary}")

        return {"ok": True, "date": today, "path": str(note_path), "summary": summary}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── Project Scaffolding & Council Box ─────────────────────────────────────────
import datetime as _dt

PROJECTS_DIR = Path("/mnt/data/Matrix-Production/projects")
VAULT_DIR    = Path.home() / "mnt/data/New-matrix-vault"

class ProjectReq(BaseModel):
    name: str
    service: str
    brief: str = ""
    indepth: str = ""
    tools: list = []
    build_prefs: str = ""

@app.post("/projects/create")
def projects_create(req: ProjectReq, _=Depends(require_auth)):
    try:
        # Map service to folder
        service_map = {
            "AI Smart Websites":        "websites",
            "AI Chatbots & Text Bots":  "chatbots",
            "AI Voice Bots":            "voicebots",
            "IVR Phone Systems":        "voicebots",
            "AI Agents":                "agents",
            "AI Super Agents":          "agents",
            "AI Workflows":             "workflows",
            "AI Consulting":            "consulting",
            "AI Social Media Marketing":"marketing",
            "AI Marketing Campaigns":   "marketing",
            "AI CRM":                   "crm",
            "Cybersecurity":            "security",
        }
        folder = service_map.get(req.service, "general")
        proj_dir = Path(f"/mnt/data/Matrix-Production/projects/{folder}/{req.name.replace(' ','_').lower()}")
        proj_dir.mkdir(parents=True, exist_ok=True)

        ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        tools_str = ", ".join(req.tools) if req.tools else "Auto-select"

        md = f"""# {req.name}
> Created: {ts}
> Service: {req.service}
> Status: QUEUED
> Tools: {tools_str}

## Brief
{req.brief or "No brief provided."}

## In-Depth Description
{req.indepth or "No detailed description provided."}

## Build Preferences
{req.build_prefs or "None specified."}

## Sub-Agent Tasks
- [ ] Analysis & Planning
- [ ] Design & Architecture
- [ ] Implementation
- [ ] QA & Testing
- [ ] Deployment

## Notes
"""
        scope_file = proj_dir / "project_scope.md"
        scope_file.write_text(md)

        return {
            "ok": True,
            "path": str(scope_file),
            "folder": folder,
            "name": req.name,
            "message": f"Project scope created at {scope_file}"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/projects/list")
def projects_list(_=Depends(require_auth)):
    try:
        base = Path("/mnt/data/Matrix-Production/projects")
        projects = []
        if base.exists():
            for service_dir in sorted(base.iterdir()):
                if service_dir.is_dir():
                    for proj_dir in sorted(service_dir.iterdir(), reverse=True):
                        scope = proj_dir / "project_scope.md"
                        if scope.exists():
                            lines = scope.read_text().split("\n")
                            brief = ""
                            for l in lines:
                                if l.startswith("> Created:"): ts = l.replace("> Created:","").strip()
                                if l.startswith("> Service:"): svc = l.replace("> Service:","").strip()
                            projects.append({
                                "name": proj_dir.name,
                                "service": service_dir.name,
                                "path": str(scope)
                            })
        return {"projects": projects[:20]}
    except Exception as e:
        return {"projects": [], "error": str(e)}

class CouncilReq(BaseModel):
    content: str
    content_type: str = "text"  # text, url, file

@app.post("/council/analyze")
async def council_analyze(req: CouncilReq, _=Depends(require_auth)):
    try:
        council_prompt = f"""You are the Elite Nexus AI Strategic Council. Analyze this project brief from 4 perspectives:

**INPUT:**
{req.content[:3000]}

Provide your analysis in this exact format:

## 🔧 Technical QA Lead
[Identify technical risks, architecture gaps, implementation challenges]

## 💰 ROI Financial Strategist
[Evaluate revenue potential, cost structure, ROI timeline, market fit]

## 🏗 Infrastructure Architect
[Assess scalability, tech stack choices, integration complexity]

## ⚠️ Risk Analyst
[Surface legal risks, competitive threats, execution risks, scope creep]

## ✅ Recommended Automation Vectors
[List 3-5 specific Elite Nexus AI services that apply to this project]

## 📋 Optimized Project Scope Summary
[2-3 sentence executive summary of what to build and why]
"""
        # Use vLLM for council analysis (free, powerful)
        payload = {
            "model": "qwen2.5-72b",
            "messages": [{"role": "user", "content": council_prompt}],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        import requests as _req
        r = _req.post("http://localhost:8000/v1/chat/completions",
                      json=payload, timeout=120)
        r.raise_for_status()
        analysis = r.json()["choices"][0]["message"]["content"]
        return {"ok": True, "analysis": analysis}
    except Exception as e:
        return {"ok": False, "error": str(e), "analysis": f"Council analysis failed: {e}"}





# -- Neural Brain Vault Visualization
@app.get('/brain/map')
def brain_map(_=Depends(require_auth)):
    import datetime as _dt4
    try:
        knowledge_files = _vault_list_files(VAULT_KNOWLEDGE)
        production_files = _vault_list_files(VAULT_PRODUCTION)
        now = _time.time()
        day = 86400
        def firing(f):
            age = now - f.get('modified', now)
            if age < day: return round(0.8 + (0.2 * (1 - age/day)), 2)
            if age < day*7: return round(0.3 + (0.5 * (1 - age/(day*7))), 2)
            return round(0.05 + (0.25 * max(0, 1 - age/(day*30))), 2)
        def region(f, vault):
            name = f.get('name','').lower()
            path = f.get('path','').lower()
            if 'daily' in path: return 'motor'
            if 'knowledge' in path: return 'prefrontal'
            if 'skill' in path: return 'associative'
            if 'project' in path or vault=='production': return 'sensory'
            if 'cfo' in path or 'factory' in path: return 'brainstem'
            if 'security' in path: return 'reflex'
            return 'concept'
        regions = {'prefrontal':[],'motor':[],'sensory':[],'associative':[],'brainstem':[],'reflex':[],'concept':[],'cerebellum':[]}
        for f in knowledge_files:
            r = region(f, 'knowledge')
            regions[r].append({'name':f['name'],'firing':firing(f),'vault':'knowledge','path':f['path']})
        for f in production_files:
            r = region(f, 'production')
            regions[r].append({'name':f['name'],'firing':firing(f),'vault':'production','path':f['path']})
        total_nodes = len(knowledge_files) + len(production_files)
        avg_firing = round(sum(firing(f) for f in knowledge_files+production_files) / max(1,total_nodes), 3)
        return {'regions':regions,'total_nodes':total_nodes,'avg_firing':avg_firing,'ts':now}
    except Exception as e:
        return {'regions':{},'error':str(e)}

# -- Wake Word Endpoint
class WakeReq(BaseModel):
    word: str
    ts: float = 0.0

@app.post('/wake/trigger')
def wake_trigger(req: WakeReq, _=Depends(require_auth)):
    print(f'WAKE WORD: {req.word}')
    return {'ok': True, 'word': req.word, 'action': 'focus_hud'}

@app.get('/wake/status')
def wake_status(_=Depends(require_auth)):
    import subprocess
    pid_file = '/tmp/wake_word.pid'
    running = False
    try:
        pid = open(pid_file).read().strip()
        subprocess.check_output(['kill', '-0', pid])
        running = True
    except: pass
    return {'running': running}

# -- Vault Assignment System
VAULT_ASSIGNMENTS_FILE = Path.home() / '.hermes' / 'vault_assignments.json'

def _load_vault_assignments():
    if VAULT_ASSIGNMENTS_FILE.exists():
        try:
            return json.loads(VAULT_ASSIGNMENTS_FILE.read_text())
        except: pass
    defaults = {}
    for aid in ['hermes-ceo','website-architect','chatbot-engineer','voice-systems-eng','agent-architect','automation-eng','ai-consultant','social-media-head','crm-marketing-head','security-head','cfo-agent','marketing-campaigns']:
        defaults[aid] = {'daily_notes':'New-matrix-vault/daily','projects':'Matrix-Production/projects','knowledge':'New-matrix-vault/knowledge','auto_chunk':True,'chunk_size':450,'chapter_split':True,'auto_summary':True}
    defaults['cfo-agent']['knowledge'] = 'Matrix-Production/projects/cfo/research'
    defaults['cfo-agent']['projects'] = 'Matrix-Production/projects/cfo'
    return defaults

def _save_vault_assignments(a):
    VAULT_ASSIGNMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    VAULT_ASSIGNMENTS_FILE.write_text(json.dumps(a, indent=2))

class VaultAssignReq(BaseModel):
    agent_id: str
    daily_notes: str = ''
    projects: str = ''
    knowledge: str = ''
    auto_chunk: bool = True
    chunk_size: int = 450
    chapter_split: bool = True
    auto_summary: bool = True

@app.get('/vault/assign')
def vault_assign_get(_=Depends(require_auth)):
    return {'assignments': _load_vault_assignments()}

@app.post('/vault/assign')
def vault_assign_set(req: VaultAssignReq, _=Depends(require_auth)):
    try:
        a = _load_vault_assignments()
        if req.agent_id not in a: a[req.agent_id] = {}
        if req.daily_notes: a[req.agent_id]['daily_notes'] = req.daily_notes
        if req.projects: a[req.agent_id]['projects'] = req.projects
        if req.knowledge: a[req.agent_id]['knowledge'] = req.knowledge
        a[req.agent_id]['auto_chunk'] = req.auto_chunk
        a[req.agent_id]['chunk_size'] = req.chunk_size
        a[req.agent_id]['chapter_split'] = req.chapter_split
        a[req.agent_id]['auto_summary'] = req.auto_summary
        _save_vault_assignments(a)
        return {'ok': True, 'config': a[req.agent_id]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

# -- Factory Management + CFO Dashboard
import sqlite3 as _sq2
FACTORY_DB = Path('/mnt/data/ai_factory/factory_state.db')
FACTORY_DIR = Path('/mnt/data/ai_factory')

def _factory_db_init():
    FACTORY_DIR.mkdir(parents=True, exist_ok=True)
    con = _sq2.connect(str(FACTORY_DB))
    con.execute('CREATE TABLE IF NOT EXISTS factories (id TEXT PRIMARY KEY, name TEXT, status TEXT, revenue_today REAL, revenue_week REAL, revenue_month REAL, products INTEGER, sales INTEGER, last_run REAL, notes TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS revenue_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, factory_id TEXT, amount REAL, platform TEXT, product TEXT)')
    cur = con.execute('SELECT COUNT(*) FROM factories').fetchone()
    if cur[0] == 0:
        factories = [
            ('factory-alpha', 'Identity POD Store', 'PROD', 127.40, 438.20, 1842.30, 47, 14, 0, 'Gothic/Techwear/Cyberpunk'),
            ('factory-beta',  'Stream Asset Factory', 'PROD', 89.20, 312.80, 1204.60, 31, 9, 0, 'Twitch/YouTube overlays'),
            ('factory-3',     'Gothic Digital Press', 'IDLE', 0.0, 0.0, 0.0, 0, 0, 0, 'Dark academia planners'),
            ('factory-4',     'Developer Utility Lab', 'IDLE', 0.0, 0.0, 0.0, 0, 0, 0, 'LLM prompt workbooks'),
            ('factory-5',     'Vector Crafting House', 'IDLE', 0.0, 0.0, 0.0, 0, 0, 0, 'SVG cut files'),
        ]
        con.executemany('INSERT INTO factories VALUES (?,?,?,?,?,?,?,?,?,?)', factories)
        con.commit()
    con.close()

_factory_db_init()

@app.get('/factory/status')
def factory_status(_=Depends(require_auth)):
    try:
        con = _sq2.connect(str(FACTORY_DB))
        rows = con.execute('SELECT * FROM factories ORDER BY revenue_month DESC').fetchall()
        con.close()
        factories = []
        total_today = total_week = total_month = 0.0
        for r in rows:
            factories.append({'id':r[0],'name':r[1],'status':r[2],'revenue_today':r[3],'revenue_week':r[4],'revenue_month':r[5],'products':r[6],'sales':r[7],'notes':r[9]})
            total_today += r[3]; total_week += r[4]; total_month += r[5]
        return {'factories':factories,'totals':{'today':round(total_today,2),'week':round(total_week,2),'month':round(total_month,2),'goal':10000.0,'progress_pct':round((total_month/10000)*100,1)}}
    except Exception as e:
        return {'factories':[],'error':str(e)}

class FactoryUpdateReq(BaseModel):
    factory_id: str
    revenue_today: float = 0.0
    revenue_week: float = 0.0
    revenue_month: float = 0.0
    products: int = 0
    sales: int = 0
    status: str = ''
    notes: str = ''

@app.post('/factory/update')
def factory_update(req: FactoryUpdateReq, _=Depends(require_auth)):
    try:
        con = _sq2.connect(str(FACTORY_DB))
        updates = []; params = []
        if req.revenue_today: updates.append('revenue_today=?'); params.append(req.revenue_today)
        if req.revenue_week: updates.append('revenue_week=?'); params.append(req.revenue_week)
        if req.revenue_month: updates.append('revenue_month=?'); params.append(req.revenue_month)
        if req.products: updates.append('products=?'); params.append(req.products)
        if req.sales: updates.append('sales=?'); params.append(req.sales)
        if req.status: updates.append('status=?'); params.append(req.status)
        if updates:
            params.append(req.factory_id)
            con.execute(f'UPDATE factories SET {",".join(updates)} WHERE id=?', params)
            con.commit()
        con.close()
        return {'ok':True}
    except Exception as e:
        return {'ok':False,'error':str(e)}

@app.post('/factory/cfo-brief')
async def factory_cfo_brief(_=Depends(require_auth)):
    import requests as _rq6
    try:
        con = _sq2.connect(str(FACTORY_DB))
        rows = con.execute('SELECT * FROM factories').fetchall()
        con.close()
        summary = chr(10).join([f'- {r[1]} ({r[2]}): today ${r[3]:.2f}, week ${r[4]:.2f}, month ${r[5]:.2f}, {r[6]} products, {r[7]} sales' for r in rows])
        prompt = f'You are the CFO Agent at Elite Nexus AI. Analyze this factory data and give a concise strategic brief under 200 words:\n\n{summary}\n\nMonthly goal: $10,000\n\nProvide: 1) Performance assessment 2) Top factory analysis 3) 3 actions to boost revenue this week 4) Any risk flags. Be direct and data-driven.'
        payload = {'model':'qwen2.5-72b','messages':[{'role':'user','content':prompt}],'stream':False,'temperature':0.7,'max_tokens':400}
        r = _rq6.post('http://localhost:8000/v1/chat/completions', json=payload, timeout=60)
        r.raise_for_status()
        brief = r.json()['choices'][0]['message']['content']
        return {'ok':True,'brief':brief}
    except Exception as e:
        return {'ok':False,'error':str(e)}

# ── Telemetry endpoints ────────────────────────────────────────────────────────
@app.get("/telemetry/session")
def telemetry_session(_=Depends(require_auth)):
    return _tel_session()

@app.post("/telemetry/reset")
def telemetry_reset(_=Depends(require_auth)):
    try:
        con = sqlite3.connect(_TEL_DB)
        today_start = _time.time() - (_time.time() % 86400)
        con.execute("DELETE FROM ledger WHERE ts>=?", (today_start,))
        con.commit(); con.close()
        return {"ok": True, "message": "Today's telemetry reset"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/vaults")
def vaults(_=Depends(require_auth)):
    return [_scan_vault(p) for p in VAULT_PATHS[:2]]

@app.get("/personas")
def personas_list(_=Depends(require_auth)):
    return {"default": DEFAULT_PERSONA, "personas": [{"key":k,"label":k.replace("-"," ").title()} for k in PERSONAS]}

# ── Chat stream ────────────────────────────────────────────────────────────────
class ChatMsg(BaseModel):
    role: str; content: str

class ChatReq(BaseModel):
    messages: list[ChatMsg]
    model: str | None = None
    persona: str | None = None

@app.post("/chat/stream")
def chat_stream(req: ChatReq, _=Depends(require_auth)):
    import subprocess, re as _re
    from pathlib import Path
    model = req.model or DEFAULT_MODEL
    persona_key = (req.persona or DEFAULT_PERSONA).lower()
    persona_prompt = PERSONAS.get(persona_key) or PERSONAS[DEFAULT_PERSONA]
    msgs = [m for m in req.messages if m.role != "system"]
    if not msgs:
        return StreamingResponse(
            iter(["event: error\ndata: {\"error\":\"no messages\"}\n\n"]),
            media_type="text/event-stream")
    last_msg = msgs[-1].content
    no_tts = " IMPORTANT: Do NOT use text_to_speech, edge-tts, speak, or any TTS tools. Do NOT run mpv or play audio files. The HUD handles all audio output via Piper TTS. When opening URLs in browser always use the EXACT URL requested - never substitute or redirect to a different site. Use xdg-open for browser navigation."
    query = "[System: " + persona_prompt[:300] + no_tts + "]\n\n" + last_msg
    HERMES_DIR = Path.home() / "hermes-agent"
    HERMES_CLI = str(HERMES_DIR / "cli.py")
    SESSION_FILE = Path.home() / ".hermes" / "matrix_hud_session.json"
    OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "OPENROUTER_KEY_HERE")
    def get_session():
        try:
            if SESSION_FILE.exists():
                return json.loads(SESSION_FILE.read_text()).get("session_id")
        except:
            pass
        return None
    def save_session(sid):
        try:
            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            SESSION_FILE.write_text(json.dumps({"session_id": sid}))
        except:
            pass
    def clean_output(text):
        text = _re.sub(r"\x1b[^m]*m", "", text)
        text = _re.sub(r"[\u2500-\u257f]", "", text)
        skip = _re.compile(r"Initializing agent|Resume this session|Session:|Duration:|Messages:|Query:|^\s*INFO:|hermes --resume")
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if not s or skip.search(s):
                continue
            lines.append(s)
        return "\n".join(lines)
    def gen():
        session_id = get_session()
        # Smart routing
        if ROUTER_AVAILABLE:
            forced = req.model if req.model and req.model != DEFAULT_MODEL else None
            route = select_model(last_msg, force_model=forced)
        else:
            route = {"provider": "openrouter", "name": "anthropic/claude-sonnet-4"}
        provider = route["provider"]
        model_name = route["name"]
        env = dict(os.environ)
        env["HERMES_QUIET"] = "1"
        env["OPENROUTER_API_KEY"] = OPENROUTER_KEY
        env["PYTHONPATH"] = str(HERMES_DIR)
        env["DISPLAY"] = ":0"
        env["DBUS_SESSION_BUS_ADDRESS"] = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
        # LOCAL OLLAMA - direct API call (fast, no Hermes overhead)
        if provider == "ollama":
            try:
                _oll_chunks = []
                payload = {"model": model_name,
                           "messages": [{"role":"system","content":persona_prompt+no_tts}] + [{"role":m.role,"content":m.content} for m in msgs],
                           "stream": True, "options": {"temperature": 0.7}}
                with requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    for line in r.iter_lines(decode_unicode=True):
                        if not line: continue
                        try: obj = json.loads(line)
                        except: continue
                        chunk = (obj.get("message") or {}).get("content") or ""
                        if chunk: _oll_chunks.append(chunk); yield f"event: token\ndata: {json.dumps({'text':chunk})}\n\n"
                        if obj.get("done"):
                            _tok = max(1, obj.get("eval_count") or len("".join(_oll_chunks)) // 4)
                            _cost = _tel_log(model_name, "ollama", _tok, persona_key)
                            yield f"event: done\ndata: {json.dumps({'model':model_name,'persona':persona_key,'tokens':_tok,'cost':_cost})}\n\n"; return
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error':str(e)[:300]})}\n\n"
            return
        # LOCAL vLLM - direct API call (fast)
        if provider == "vllm":
            try:
                _vllm_chunks = []
                payload = {"model": model_name,
                           "messages": [{"role":"system","content":persona_prompt+no_tts}] + [{"role":m.role,"content":m.content} for m in msgs],
                           "stream": True, "temperature": 0.7, "max_tokens": 2048}
                with requests.post("http://localhost:8000/v1/chat/completions", json=payload, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    for line in r.iter_lines(decode_unicode=True):
                        if not line or line == "data: [DONE]": continue
                        if line.startswith("data: "):
                            try:
                                obj = json.loads(line[6:])
                                chunk = (obj.get("choices",[{}])[0].get("delta") or {}).get("content") or ""
                                if chunk: _vllm_chunks.append(chunk); yield f"event: token\ndata: {json.dumps({'text':chunk})}\n\n"
                                if (obj.get("choices",[{}])[0].get("finish_reason")) == "stop":
                                    _tok = max(1, len("".join(_vllm_chunks)) // 4)
                                    _cost = _tel_log(model_name, "vllm", _tok, persona_key)
                                    yield f"event: done\ndata: {json.dumps({'model':model_name,'persona':persona_key,'tokens':_tok,'cost':_cost})}\n\n"; return
                            except: continue
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error':str(e)[:300]})}\n\n"
            return
        # CLAUDE CODE CLI
        if provider == "claude_code_cli":
            cmd = ["claude", "--print", "--no-markdown", last_msg]
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1, env=env)
                _cc_lines = []
                for line in proc.stdout:
                    if line.strip(): _cc_lines.append(line); yield f"event: token\ndata: {json.dumps({'text':line})}\n\n"
                proc.wait()
                _tok = max(1, sum(len(l) for l in _cc_lines) // 4)
                _cost = _tel_log("claude-code", "claude_code_cli", _tok, persona_key)
                yield f"event: done\ndata: {json.dumps({'model':'claude-code','persona':persona_key,'tokens':_tok,'cost':_cost})}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error':str(e)[:300]})}\n\n"
            return
        # CLOUD - Hermes CLI with tools
        cmd = ["/usr/bin/python3", HERMES_CLI,
               "--query", query,
               "--model", model_name,
               "--provider", "openrouter",
               "--skills", "google-workspace",
               "--quiet"]
        if session_id:
            cmd.extend(["--resume", session_id])
        try:
            yield "event: token\ndata: {\"text\":\"\u29d7 Hermes thinking...\"}\n\n"
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=str(HERMES_DIR), env=env, text=True, bufsize=1)
            full_out = []
            cleared = False
            for line in proc.stdout:
                full_out.append(line)
                clean = clean_output(line)
                if not clean:
                    continue
                if not cleared:
                    yield "event: token\ndata: {\"text\":\"\r\"}\n\n"
                    cleared = True
                yield "event: token\ndata: " + json.dumps({"text": clean + " "}) + "\n\n"
            proc.wait()
            full_text = "".join(full_out)
            m = _re.search(r"--resume\s+(\S+)", full_text)
            if m:
                save_session(m.group(1))
            _tok = max(1, len(" ".join(full_out)) // 4)
            _cost = _tel_log(model_name, "openrouter", _tok, persona_key)
            yield "event: done\ndata: " + json.dumps({"model": model_name, "persona": persona_key, "tokens": _tok, "cost": _cost}) + "\n\n"
        except Exception as e:
            yield "event: error\ndata: " + json.dumps({"error": str(e)[:300]}) + "\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ── Vision chat ────────────────────────────────────────────────────────────────
class VisionReq(BaseModel):
    prompt: str
    image_b64: str
    model: str = "llama3.2-vision:latest"
    persona: str = "lara-croft"

@app.post("/vision")
def vision_chat(req: VisionReq, _=Depends(require_auth)):
    persona_prompt = PERSONAS.get(req.persona) or PERSONAS[DEFAULT_PERSONA]
    payload = {
        "model": req.model,
        "messages": [
            {"role":"system","content": persona_prompt},
            {"role":"user","content": req.prompt, "images": [req.image_b64]}
        ],
        "stream": False, "options": {"temperature": 0.7}
    }
    def gen():
        try:
            with requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=120) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line: continue
                    try: obj = json.loads(line)
                    except: continue
                    chunk = (obj.get("message") or {}).get("content") or ""
                    if chunk: yield f"event: token\ndata: {json.dumps({'text':chunk})}\n\n"
                    if obj.get("done"): yield f"event: done\ndata: {{}}\n\n"; return
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error':str(e)[:300]})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

# ── Piper TTS ──────────────────────────────────────────────────────────────────
class TtsReq(BaseModel):
    text: str; voice: str | None = None

@app.post("/tts/piper")
def tts_piper(req: TtsReq, _=Depends(require_auth)):
    voice = req.voice or PIPER_VOICE
    if not voice or not Path(voice).exists():
        raise HTTPException(503, f"Piper voice not found: {voice}")
    text = _strip_tts(req.text or "")
    if not text: raise HTTPException(400, "empty text")
    try:
        proc = subprocess.run(
            [PIPER_BIN,"--model",voice,"--output_file","-"],
            input=text.encode("utf-8"), capture_output=True, timeout=30, check=True
        )
    except FileNotFoundError: raise HTTPException(503, "piper binary not found")
    except subprocess.CalledProcessError as e: raise HTTPException(500, f"piper failed: {e.stderr.decode()[:200]}")
    wav = proc.stdout
    if not wav or len(wav) < 64: raise HTTPException(500, "piper returned empty audio")
    return Response(content=wav, media_type="audio/wav")

# ── Edge TTS ───────────────────────────────────────────────────────────────────
class EdgeTtsReq(BaseModel):
    text: str; voice: str = "en-GB-SoniaNeural"

@app.post("/tts/edge")
async def tts_edge(req: EdgeTtsReq, _=Depends(require_auth)):
    import edge_tts
    text = _strip_tts(req.text or "")
    if not text: raise HTTPException(400, "empty text")
    communicate = edge_tts.Communicate(text, req.voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": buf.write(chunk["data"])
    audio = buf.getvalue()
    if not audio: raise HTTPException(500, "edge-tts returned no audio")
    return Response(content=audio, media_type="audio/mpeg")

# ── STT (Whisper) ──────────────────────────────────────────────────────────────
class SttReq(BaseModel):
    base64audio: str; mimetype: str = "audio/webm"

@app.post("/stt")
def stt(req: SttReq, _=Depends(require_auth)):
    import whisper
    audio_bytes = base64.b64decode(req.base64audio)
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes); tmp = f.name
    try:
        model = whisper.load_model("tiny")
        result = model.transcribe(tmp, language="en")
        return {"text": result["text"].strip()}
    finally:
        try: os.unlink(tmp)
        except: pass

# ── Terminal run ───────────────────────────────────────────────────────────────
class RunReq(BaseModel):
    command: str

@app.post("/run")
def run_command(req: RunReq, _=Depends(require_auth)):
    cmd = req.command.strip()
    if not cmd: raise HTTPException(400, "empty command")
    blocked = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){:|:&};:"]
    for b in blocked:
        if b in cmd: raise HTTPException(403, f"blocked: {b}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=str(Path.home()))
        return {"output": result.stdout, "error": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired: raise HTTPException(408, "timed out")
    except Exception as e: raise HTTPException(500, str(e))


# ── Webcam ────────────────────────────────────────────────────────────────────
@app.get("/webcam/capture")
def webcam_capture(_=Depends(require_auth)):
    import cv2, base64, time
    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return {"ok": False, "error": "Webcam capture failed"}
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf).decode()
        return {"ok": True, "image_b64": b64, "width": int(frame.shape[1]), "height": int(frame.shape[0])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class WebcamAnalyzeReq(BaseModel):
    prompt: str = "Describe in detail what you see. Be specific about people, objects, text, colors, and spatial relationships."

@app.post("/webcam/analyze")
def webcam_analyze(req: WebcamAnalyzeReq, _=Depends(require_auth)):
    import cv2, base64, time, subprocess, tempfile, re as _re
    from pathlib import Path
    OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "OPENROUTER_KEY_HERE")
    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return {"ok": False, "error": "Webcam capture failed"}
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        cv2.imwrite(tmp.name, frame)
        tmp.close()
        HERMES_DIR = Path.home() / "hermes-agent"
        HERMES_CLI = str(HERMES_DIR / "cli.py")
        SESSION_FILE = Path.home() / ".hermes" / "matrix_hud_session.json"
        cmd = ["/usr/bin/python3", HERMES_CLI,
               "--query", req.prompt,
               "--image", tmp.name,
               "--model", "anthropic/claude-sonnet-4",
               "--provider", "openrouter",
               "--skills", "google-workspace",
               "--quiet"]
        try:
            sid = json.loads(SESSION_FILE.read_text()).get("session_id") if SESSION_FILE.exists() else None
            if sid: cmd.extend(["--resume", sid])
        except:
            pass
        env = dict(os.environ)
        env["HERMES_QUIET"] = "1"
        env["OPENROUTER_API_KEY"] = OPENROUTER_KEY
        env["PYTHONPATH"] = str(HERMES_DIR)
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(HERMES_DIR), env=env, timeout=90)
        output = proc.stdout
        output = _re.sub(r"\x1b[^m]*m", "", output)
        output = _re.sub(r"[\u2500-\u257f]", "", output)
        skip = _re.compile(r"Initializing agent|Resume this session|Session:|Duration:|Messages:|Query:|^\s*INFO:|hermes --resume")
        lines = [s.strip() for s in output.splitlines() if s.strip() and not skip.search(s.strip())]
        clean = " ".join(lines)
        os.unlink(tmp.name)
        return {"ok": True, "description": clean}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


# ── LLM Router Info ────────────────────────────────────────────────────────────
@app.get("/router/info")
def router_info(q: str = "", _=Depends(require_auth)):
    if not ROUTER_AVAILABLE:
        return {"available": False}
    info = get_routing_info(q) if q else {"available": True}
    info["available"] = True
    return info

@app.get("/router/models")
def router_models(_=Depends(require_auth)):
    from llm_router import MODELS, vllm_available, ollama_model_available
    status = {}
    for key, m in MODELS.items():
        available = False
        if m["provider"] == "ollama":
            available = ollama_model_available(m["name"])
        elif m["provider"] == "vllm":
            available = vllm_available()
        elif m["provider"] in ("openrouter", "claude_code_cli"):
            available = True
        status[key] = {**m, "available": available}
    return status


# ── Morning Briefing ───────────────────────────────────────────────────────────
@app.post("/briefing/morning")
def morning_briefing_endpoint(_=Depends(require_auth)):
    import subprocess, re as _re
    from pathlib import Path
    from datetime import datetime
    HERMES_DIR = Path.home() / "hermes-agent"
    HERMES_CLI = str(HERMES_DIR / "cli.py")
    OPENROUTER_KEY_MB = os.environ.get("OPENROUTER_API_KEY", "")
    now = datetime.now()
    query = (
        f"Good morning! Today is {now.strftime('%A, %B %d, %Y')} at {now.strftime('%I:%M %p')}. "
        f"Please give me a morning briefing: "
        f"1) Check my Gmail for any urgent or important unread emails (last 24h) "
        f"2) Check my Google Calendar for today's events and upcoming appointments this week "
        f"3) Give me a motivational productivity note for the day. "
        f"Keep it concise and actionable. Format it clearly."
    )
    cmd = ["/usr/bin/python3", HERMES_CLI,
           "--query", query,
           "--model", "anthropic/claude-sonnet-4",
           "--provider", "openrouter",
           "--skills", "google-workspace",
           "--quiet"]
    env = dict(os.environ)
    env["HERMES_QUIET"] = "1"
    env["OPENROUTER_API_KEY"] = OPENROUTER_KEY_MB
    env["PYTHONPATH"] = str(HERMES_DIR)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              cwd=str(HERMES_DIR), env=env, timeout=120)
        output = proc.stdout
        output = _re.sub(r"\x1b[^m]*m", "", output)
        output = _re.sub(r"[\u2500-\u257f]", "", output)
        skip = _re.compile(r"Initializing agent|Resume this session|Session:|Duration:|Messages:|Query:|^\s*INFO:|hermes --resume")
        lines = [s.strip() for s in output.splitlines() if s.strip() and not skip.search(s.strip())]
        clean = " ".join(lines)
        return {"ok": True, "briefing": clean}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}



# ── YouTube Playlists ──────────────────────────────────────────────────────────
YOUTUBE_PLAYLISTS = {
    'elite nexus': 'https://www.youtube.com/watch?v=r13L1YJ3sts&list=PLDokTh_uT5E3e4l1Sk4mQzwM2aUMOSyLi',
    'nexus': 'https://www.youtube.com/watch?v=r13L1YJ3sts&list=PLDokTh_uT5E3e4l1Sk4mQzwM2aUMOSyLi',
    'watch later': 'https://www.youtube.com/watch?v=ntvkDnk_5jA&list=WL',
    'wl': 'https://www.youtube.com/watch?v=ntvkDnk_5jA&list=WL',
    'liked': 'https://www.youtube.com/watch?v=za6sYoYE29I&list=LL',
    'liked videos': 'https://www.youtube.com/watch?v=za6sYoYE29I&list=LL',
    'll': 'https://www.youtube.com/watch?v=za6sYoYE29I&list=LL',
}

@app.get("/youtube/playlists")
def youtube_playlists(_=Depends(require_auth)):
    return YOUTUBE_PLAYLISTS

@app.post("/youtube/open")
def youtube_open(req: dict, _=Depends(require_auth)):
    import subprocess
    name = (req.get("name") or "").lower().strip()
    url = YOUTUBE_PLAYLISTS.get(name)
    if not url:
        # fuzzy match
        for key in YOUTUBE_PLAYLISTS:
            if key in name or name in key:
                url = YOUTUBE_PLAYLISTS[key]
                break
    if url:
        env = dict(os.environ)
        env["DISPLAY"] = ":0"
        env["DBUS_SESSION_BUS_ADDRESS"] = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
        subprocess.Popen(["xdg-open", url], env=env)
        return {"ok": True, "opened": url}
    return {"ok": False, "error": f"Playlist not found: {name}", "available": list(YOUTUBE_PLAYLISTS.keys())}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BRIDGE_PORT", "8765"))
    uvicorn.run("bridge:app", host="0.0.0.0", port=port, log_level="info")
