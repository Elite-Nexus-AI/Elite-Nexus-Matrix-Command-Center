#!/usr/bin/env bash
# Elite Nexus vLLM Server Launcher
# Serves Qwen2.5-72B-Instruct across dual RTX 3090 (48GB combined VRAM)
# Runs on port 8000 with OpenAI-compatible API

MODEL_PATH="/mnt/data/models/Qwen2.5-72B-Instruct"
LOG_FILE="/tmp/vllm_server.log"
PORT=8000
HOST="0.0.0.0"

# Check if model exists
if [ ! -d "$MODEL_PATH" ]; then
    echo "ERROR: Model not found at $MODEL_PATH"
    echo "Download status:"
    cat /tmp/qwen_download.log | tail -5 2>/dev/null || echo "No download log found"
    exit 1
fi

# Check if already running
if curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; then
    echo "vLLM already running on port $PORT"
    curl -s http://localhost:$PORT/v1/models | python3 -m json.tool
    exit 0
fi

echo "Starting vLLM server..."
echo "Model: $MODEL_PATH"
echo "GPUs: 2x RTX 3090 (tensor_parallel_size=2)"
echo "Port: $PORT"
echo "Log: $LOG_FILE"
echo ""

# Export HuggingFace cache location
export HF_HOME=/mnt/data/vllm_cache
export CUDA_VISIBLE_DEVICES=0,1

# Launch vLLM with tensor parallelism across both GPUs
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 32768 \
    --served-model-name "qwen2.5-72b" \
    --trust-remote-code \
    --disable-log-stats \
    > "$LOG_FILE" 2>&1 &

VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"
echo $VLLM_PID > /tmp/vllm.pid

echo "Waiting for server to start (this takes ~60-90 seconds for 72B model)..."

for i in $(seq 1 60); do
    sleep 3
    if curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; then
        echo ""
        echo "vLLM server ONLINE after ${i}x3 seconds"
        curl -s http://localhost:$PORT/v1/models | python3 -m json.tool
        exit 0
    fi
    printf "."
done

echo ""
echo "Server still loading — check: tail -f $LOG_FILE"
echo "Test with: curl http://localhost:$PORT/v1/models"
