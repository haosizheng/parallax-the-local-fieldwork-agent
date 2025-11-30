#!/bin/bash

# Parallax 调度器启动脚本（使用 HuggingFace 镜像）
# 解决中国大陆访问 HuggingFace 的网络问题

echo "🚀 正在启动 Parallax 调度器（使用镜像源）..."
echo ""

# 进入项目目录
cd /Users/shibi/Documents/cursor-test/gradient/parallax

# 激活虚拟环境
source venv/bin/activate

# 设置 HuggingFace 镜像源
export HF_ENDPOINT=https://hf-mirror.com
echo "✅ 已设置 HuggingFace 镜像: $HF_ENDPOINT"

# 设置下载超时时间（更长）
export HF_HUB_DOWNLOAD_TIMEOUT=300
echo "✅ 已设置下载超时: 300 秒"

# 启动调度器
echo "🎯 正在启动调度器..."
echo ""

parallax run -m mlx-community/Qwen3-0.6B-bf16 -n 1
