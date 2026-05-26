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
