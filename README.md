# The Digital Tribunal

A Cyberpunk-themed AI Judgment System powered by Parallax. This tool allows users to confess their "sins" and receive philosophical verdicts from multiple AI agents, culminating in a final judgment from the High Judge. It features a RAG (Retrieval-Augmented Generation) system for injecting custom knowledge into the judges.

## Prerequisites

- Python 3.10+
- Parallax Framework
- Dependencies: `nicegui`, `openai`, `chromadb`, `sentence_transformers`, `pypdf`

## Quick Start

You need to run three separate terminal processes to start the full system.

### 1. Start the Scheduler (Terminal 1)
This manages the P2P network and the API endpoint.
```bash
./start_dolphin.sh
```
*   **Port:** 8888 (P2P), 3001 (OpenAI API)

### 2. Start the Compute Node (Terminal 2)
This runs the actual LLM (Qwen2-7B) and connects to the Scheduler.
```bash
./start_node.sh
```
*   **Port:** 3000 (Internal Model Server)

### 3. Start the Tribunal UI (Terminal 3)
This launches the web interface.
```bash
source venv/bin/activate
python3 src/tribunal/main.py
```
*   **Port:** 8081 (Web UI)
*   **Access:** Open [http://localhost:8081](http://localhost:8081) in your browser.

## Port Management & Troubleshooting

If you encounter "Address already in use" errors, use the following commands to identify and kill the stuck processes.

### Ports Used
- **8081**: Tribunal Web UI (Python/NiceGUI)
- **3001**: Parallax Scheduler API (Python)
- **3000**: Parallax Node Internal Server (Python)
- **8888**: Parallax P2P Communication (Python)

### How to Clean Up Ports

**Option 1: The "Nuke" Method (Recommended for Dev)**
Kills all Python processes. Use with caution if you have other Python scripts running.
```bash
pkill -9 python3
```

**Option 2: Surgical Removal (By Port)**
Check who is using a specific port (e.g., 3001):
```bash
lsof -i :3001
```
Kill the process by PID:
```bash
kill -9 <PID>
```

**One-liner to kill process on a specific port (e.g., 8081):**
```bash
lsof -t -i:8081 | xargs kill -9
```

### Common Issues
- **"No route to host" / VPN Issues**: The system is configured to bind to `localhost` to avoid VPN interference. Do not remove `PARALLAX_HOST_MADDRS` from the start scripts.
- **"Connection Refused"**: Ensure the Scheduler (`start_dolphin.sh`) is fully running before starting the Node or the UI.
- **UI Hangs on "DEPLOYING..."**: This usually means the Node hasn't successfully joined the Scheduler. Check the Node terminal for "Registered ... Block" messages.

## Features
- **Multi-Agent Analysis**: Three distinct AI personas analyze your confession.
- **Custom RAG**: Upload TXT/PDF files in the "Protocol Database" to give judges specific knowledge.
- **Interrogation Room**: Chat one-on-one with any agent after the verdict.
- **Cyberpunk UI**: Fully themed interface with terminal-style interactions.
