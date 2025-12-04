#!/bin/bash

# Parallax 节点启动脚本（使用 HuggingFace 镜像）
# 解决中国大陆访问 HuggingFace 的网络问题

echo "🚀 正在启动 Parallax 节点（使用镜像源）..."
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

# 启动节点
echo "🔗 正在连接到调度器..."
echo ""

# Force binding to localhost
export PARALLAX_HOST_MADDRS="/ip4/127.0.0.1/tcp/0"

# Manual peering: Connect to Scheduler at localhost:8888 with known Peer ID
# Peer ID from logs: 12D3KooWE2A6KUYbrkKWgYdTDNyKiBR7yyfTNywEscEtAj5GPMJq
SCHEDULER_ADDR="/ip4/127.0.0.1/tcp/8888/p2p/12D3KooWE2A6KUYbrkKWgYdTDNyKiBR7yyfTNywEscEtAj5GPMJq"

parallax join -s "$SCHEDULER_ADDR"
