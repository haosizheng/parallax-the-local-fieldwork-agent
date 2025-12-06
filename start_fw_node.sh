#!/bin/bash

# Fieldwork Agent Node
# 启动计算节点 - 步骤 2

echo "🚀 Starting Fieldwork Node..."
echo "⚠️  Make sure Scheduler (Step 1) is running first!"
echo ""

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Set HF Mirror just in case
export HF_ENDPOINT=https://hf-mirror.com

# Force binding to localhost
export PARALLAX_HOST_MADDRS="/ip4/127.0.0.1/tcp/0"

# Connect to the Scheduler at localhost:8888
# This Peer ID comes from the generated p2p.key in the project root.
# If p2p.key is deleted, this ID will change and need updating.
SCHEDULER_ID="12D3KooWE2A6KUYbrkKWgYdTDNyKiBR7yyfTNywEscEtAj5GPMJq"
SCHEDULER_ADDR="/ip4/127.0.0.1/tcp/8888/p2p/$SCHEDULER_ID"

echo "🔗 Connecting to Scheduler at: $SCHEDULER_ADDR"

parallax join -s "$SCHEDULER_ADDR"
