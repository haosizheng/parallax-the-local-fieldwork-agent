#!/bin/bash

# Fieldwork Agent App (UI)
# 启动前端界面 - 步骤 3

echo "🚀 Starting Fieldwork Agent UI..."
echo "⚠️  Make sure Scheduler and Node are running!"
echo ""

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Run Streamlit
streamlit run src/fieldwork_agent/app.py
