#!/bin/bash

# Parallax Scheduler Start Script (Dolphin 2.9.2 Qwen2 7B 4bit)

echo "🚀 Starting Parallax Scheduler (Dolphin 2.9.2 Qwen2 7B 4bit)..."
echo ""

# Enter project directory
cd /Users/shibi/Documents/cursor-test/gradient/parallax
rm -f scheduler.log

# Activate virtual environment
source venv/bin/activate

# Local model path
MODEL_PATH="/Users/shibi/Documents/cursor-test/gradient/parallax/models/mlx-community/dolphin-2.9.2-qwen2-7b-4bit"

echo "📁 Using local model: $MODEL_PATH"
echo "🎯 Starting scheduler..."
echo ""

# Force binding to localhost on fixed port 8888 for manual peering
export PARALLAX_HOST_MADDRS="/ip4/127.0.0.1/tcp/8888"

# Start scheduler
parallax run -m "$MODEL_PATH" -n 1 | tee scheduler.log
