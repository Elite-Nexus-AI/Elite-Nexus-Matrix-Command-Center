#!/usr/bin/env bash
# Deploy bridge_v2 and update config
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Copy new bridge
cp bridge_v2.py bridge.py

# Update config to point to piper voice
cat > config.sh << 'CFGEOF'
#!/usr/bin/env bash
export OLLAMA_URL="http://localhost:11434"
export MATRIX_DEFAULT_MODEL="hermes3:8b"
export MATRIX_DEFAULT_PERSONA="lara-croft"
export BRIDGE_PORT="8765"
export MATRIX_BRIDGE_TOKEN=""
export PIPER_BIN="$HOME/.local/bin/piper"
export PIPER_VOICE="$HOME/piper-voices/en_GB-jenny_dioco-medium.onnx"
export OBSIDIAN_VAULTS="$HOME/hermes-agent/skills,$HOME/hermes-agent/docs"
CFGEOF

echo "Deployed bridge_v2 → bridge.py"
echo "Piper voice: $HOME/piper-voices/en_GB-jenny_dioco-medium.onnx"
echo "Vaults: ~/hermes-agent/skills and ~/hermes-agent/docs"
