#!/bin/bash

# Parallax 调度器启动脚本（使用本地 Qwen2.5-0.5B）

echo "🚀 正在启动 Parallax 调度器（Qwen2.5-0.5B）..."
echo ""

# 进入项目目录
cd /Users/shibi/Documents/cursor-test/gradient/parallax

# 激活虚拟环境
source venv/bin/activate

# 使用本地模型路径
MODEL_PATH="/Users/shibi/.cache/modelscope/hub/models/Qwen/Qwen2___5-0___5B-Instruct"

echo "📁 使用本地模型: $MODEL_PATH"
echo "🎯 正在启动调度器..."
echo ""

# 启动调度器 - 使用本地路径
parallax run -m "$MODEL_PATH" -n 1
