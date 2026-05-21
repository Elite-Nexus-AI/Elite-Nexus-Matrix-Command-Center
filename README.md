# Elite Nexus // Matrix HUD — Perfect Clone

## Quick Start

```bash
# 1. Configure
nano config.sh   # set OBSIDIAN_VAULTS, PIPER_VOICE, API keys

# 2. Ensure Ollama is running (separate terminal)
ollama serve
ollama pull hermes3:8b   # first time only (~5GB)

# 3. Launch bridge
bash run.sh

# 4. Open browser
# http://localhost:8765
```

## If You Have No Bridge (Offline Preview)
Just open `index.html` directly in any browser.
The HUD loads with mock data so you can see the full layout.
When you're ready, click ⚙ CONFIG and enter your bridge URL + token.

## Bridge Endpoints
| Endpoint | Purpose |
|---|---|
| `GET  /health`           | Hermes + Piper status |
| `GET  /metrics/system`   | CPU, RAM, disks |
| `GET  /metrics/gpu`      | nvidia-smi stats |
| `GET  /metrics/llm`      | token usage |
| `GET  /agents`           | reads data/agents.json |
| `GET  /vaults`           | scans Obsidian vaults |
| `GET  /personas`         | persona list |
| `POST /chat/stream`      | SSE streaming (Hermes) |
| `POST /tts`              | Piper → WAV |

## Chat Commands
- `/clear` — wipe history
- `/persona <key>` — switch persona (lara-croft, jarvis, raw)
- `/persona` — show current
- `/mute` — toggle TTS
- `/help` — full help

## Keyboard
- **Enter** — send
- **Shift+Enter** — newline
- **↑/↓** — command history
- **Esc** — cancel / stop stream
- **Hold SPACE** (outside input) — push-to-talk dictation
