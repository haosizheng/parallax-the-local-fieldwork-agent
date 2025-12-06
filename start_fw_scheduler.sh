#!/bin/bash

# Fieldwork Agent Scheduler (Dolphin Model)
# 启动调度器 - 步骤 1

echo "🚀 Starting Fieldwork Scheduler (Dolphin 7B Uncensored)..."
echo "⚠️  Keep this terminal OPEN."
echo ""

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Use the symlinked local model path
MODEL_PATH="./models/mlx-community/dolphin-2.9.2-qwen2-7b-4bit"

# Check if model exists
if [ ! -L "$MODEL_PATH" ] && [ ! -d "$MODEL_PATH" ]; then
    echo "❌ Model not found at $MODEL_PATH"
    echo "Falling back to Qwen2.5-0.5B..."
    MODEL_PATH="mlx-community/Qwen2.5-0.5B-Instruct"
fi

echo "📁 Using model: $MODEL_PATH"

# Force binding to localhost on fixed port 8888
export PARALLAX_HOST_MADDRS="/ip4/127.0.0.1/tcp/8888"

# Start scheduler
# -m: Model path
# -n: Number of nodes (1 for local)
parallax run -m "$MODEL_PATH" -n 1
