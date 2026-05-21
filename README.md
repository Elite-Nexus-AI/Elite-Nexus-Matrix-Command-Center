# ⬡ Elite Nexus Matrix Command Center

> A fully local AI command center HUD — cyberpunk aesthetic, real hardware metrics, voice interaction, and agent control. No cloud. No subscriptions. Just raw intelligence running on your own silicon.

![Elite Nexus AI](https://d2xsxph8kpxj0f.cloudfront.net/310519663556295192/7jxcpmYhbWw6CFk5dJ5yBs/elite-nexus-logo-mtQyXc6r87gqejRYQZnyoo.webp)

---

## ⚡ What It Is

The Elite Nexus Matrix HUD is a browser-based AI operating system dashboard that runs entirely on your local machine. Built on top of [Hermes Agent](https://github.com/jackroberts/hermes-agent) and extended with a custom FastAPI bridge, it gives you a real-time command center with:

- **Dual GPU telemetry** — live utilization, VRAM, power draw, temp, fan speed
- **CPU / RAM / Disk metrics** — real psutil data, no fake numbers
- **LLM Chat Terminal** — streaming SSE chat via Ollama, with model switching
- **Piper TTS** — local British female voice (Jenny Dioco) with Edge-TTS fallback
- **Whisper STT** — push-to-talk mic dictation (hold SPACE)
- **Vision** — drag & drop images → routed to llama3.2-vision automatically
- **Agent Commander** — spawn, kill, and manage AI agents
- **Vault Codex** — interactive 3D galaxy visualization of your knowledge base
- **Persona System** — switch between Lara Croft, JARVIS, Athena, and raw mode
- **Model Switcher** — hot-swap between all installed Ollama models

---

## 🖥️ System Requirements

- Linux (tested on Zorin OS / Ubuntu 24)
- Python 3.12+
- [Ollama](https://ollama.ai) installed and running
- NVIDIA GPU(s) with nvidia-smi
- [Piper TTS](https://github.com/rhasspy/piper) (optional, falls back to Edge-TTS)
- A browser (Brave or Firefox)

---

## 🚀 Quick Start

```bash
git clone https://github.com/Elite-Nexus-AI/Elite-Nexus-Matrix-Command-Center.git
cd Elite-Nexus-Matrix-Command-Center

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn psutil requests edge-tts openai-whisper

# Configure
cp config.sh.example config.sh
nano config.sh  # set your Ollama URL, model, Piper path

# Launch
bash start-matrix.sh
```

Then open `http://localhost:8765` in your browser.

---

## ⚙️ Configuration

Edit `config.sh`:

```bash
export OLLAMA_URL="http://localhost:11434"
export MATRIX_DEFAULT_MODEL="hermes3:8b"
export MATRIX_DEFAULT_PERSONA="lara-croft"
export BRIDGE_PORT="8765"
export PIPER_BIN="$HOME/.local/bin/piper"
export PIPER_VOICE="$HOME/piper-voices/en_GB-jenny_dioco-medium.onnx"
export OBSIDIAN_VAULTS="$HOME/your-vault/skills,$HOME/your-vault/docs"
```

---

## 🎙️ Voice Commands

| Action | Command |
|--------|---------|
| Push to talk | Hold `SPACE` |
| Clear chat | `/clear` |
| Switch persona | `/persona lara-croft` |
| Switch model | `/model hermes3:8b` |
| Run terminal command | `/run ls -la` |
| Toggle mute | `/mute` |

---

## 🌌 Vault Codex

The dual galaxy visualizations pull from your knowledge vaults (Obsidian, markdown files). Interact with them:

- **Mouse over** — push particles away
- **Click** — explosion ripple
- **Drag** — spin the galaxy in 3D
- **Scroll** — zoom in/out
- **Hover stars** — see note labels

---

## 🤖 Personas

| Persona | Style |
|---------|-------|
| `lara-croft` | Sharp British, dry humor, mission-focused |
| `jarvis` | Formal British AI, calls you "sir" |
| `athena` | Analytical goddess of wisdom |
| `raw` | Plain helpful assistant |

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Bridge + Piper status |
| `GET /models` | All Ollama models |
| `GET /metrics/gpu` | Real nvidia-smi data |
| `GET /metrics/system` | CPU/RAM/disk |
| `POST /chat/stream` | SSE streaming chat |
| `POST /tts/piper` | Local Piper TTS |
| `POST /tts/edge` | Edge-TTS neural voice |
| `POST /stt` | Whisper transcription |
| `POST /vision` | Vision model inference |
| `GET /agents` | Agent roster |
| `POST /agents/spawn` | Create/update agent |

---

## 🏗️ Built By

**[Elite Nexus AI](https://elitenexusai.com)** — Engineering the evolution of AI systems.

---

## 📄 License

MIT — Use it, modify it, build on it.
