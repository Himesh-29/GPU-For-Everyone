# GPU Connect — Installation Guide

Complete step-by-step installation guides for all platforms.

## Table of Contents

- [Windows](#windows)
- [Linux (Raspberry Pi, Ubuntu, Debian)](#linux)
- [macOS](#macos)

---

## Windows

### Prerequisites

- **Ollama** (GPU-accelerated local inference)
- **Internet connection**

### Installation Steps

#### 1. Download the Windows Agent

Visit [gpu-connect.vercel.app](https://gpu-connect.vercel.app) and click **"Download for Windows (.exe)"** on the Integrate section, or download directly:

```ps
Invoke-WebRequest -Uri "https://gpu-connect.vercel.app/downloads/gpu-connect.exe" -OutFile "gpu-connect-agent.exe"
```

#### 2. Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com/download/windows).

Then pull a model:

```cmd
ollama pull tinyllama
```

#### 3. Run the Agent

Double-click `gpu-connect-agent.exe` or run from PowerShell:

```ps
.\gpu-connect-agent.exe
```

#### 4. Generate Your Agent Token

1. Go to [gpu-connect.vercel.app](https://gpu-connect.vercel.app)
2. Log in to your dashboard
3. Click **Provider** tab
4. Click **Generate Agent Token**
5. Copy the token (starts with `gpc_`)

#### 5. Paste the Token

When the agent prompts for your token, paste it:

```
Paste your Agent Token: gpc_xyz123...
```

#### 6. Start Earning

Your node is now live! Track earnings and job status in the **Provider Dashboard**.

---

## Linux

### Prerequisites

- **Raspberry Pi 5** (or any Linux: Ubuntu, Debian, CentOS, etc.)
- **Python 3.9+** (usually pre-installed)
- **Ollama** (for local inference)
- **SSH access** (if installing remotely)
- **Internet connection**

### Installation Steps (via SSH)

#### Step 1: SSH into your Linux machine

```bash
ssh pi@<your-pi-ip>
# or for hostname
ssh pi@raspberrypi.local
# or for Ubuntu:
ssh ubuntu@<host-ip>
```

#### Step 2: Download the Linux Agent Package

```bash
# Option A: Download from Vercel (recommended while Vercel has it)
wget https://gpu-connect.vercel.app/downloads/gpu-connect-agent-linux.zip

# Option B: Download from GitHub
wget https://github.com/Himesh-29/GPUConnect/releases/download/v2.1.0/gpu-connect-agent-linux.zip

# If wget not available, use curl:
curl -O https://gpu-connect.vercel.app/downloads/gpu-connect-agent-linux.zip
```

#### Step 3: Extract and Install

```bash
# Extract the archive
unzip gpu-connect-agent-linux.zip -d gpu-connect-agent

# Navigate to directory
cd gpu-connect-agent

# Make scripts executable
chmod +x install.sh uninstall.sh

# Run the installer (requires sudo)
sudo ./install.sh
```

The installer will:
- Create a virtual environment at `/opt/gpu-connect-agent/`
- Install systemd service for auto-start
- Create helper commands for managing the agent

#### Step 4: Install Ollama

```bash
# One-line install
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull tinyllama
```

For larger models on Raspberry Pi 5:
```bash
ollama pull phi-3-mini
ollama pull gemma:2b
```

#### Step 5: Generate Your Agent Token

From your desktop/laptop:
1. Go to [gpu-connect.vercel.app](https://gpu-connect.vercel.app)
2. Log in to your dashboard
3. Go to **Provider** tab
4. Click **Generate Agent Token**
5. Copy the token (starts with `gpc_`)

#### Step 6: Set Your Token on the Pi

Back on your Raspberry Pi via SSH:

```bash
sudo gpu-connect-token gpc_your_token_here
```

#### Step 7: Start the Agent

```bash
# Start immediately
sudo systemctl start gpu-connect-agent

# (Optional) Auto-start on boot
sudo systemctl enable gpu-connect-agent

# Check status
sudo systemctl status gpu-connect-agent
```

#### Step 8: Monitor Logs

```bash
# Live log stream
journalctl -u gpu-connect-agent -f

# Last 50 lines
journalctl -u gpu-connect-agent -n 50
```

### Quick Install (Copy-Paste All at Once)

```bash
# Download and install
wget https://gpu-connect.vercel.app/downloads/gpu-connect-agent-linux.zip
unzip gpu-connect-agent-linux.zip -d gpu-connect-agent
cd gpu-connect-agent
chmod +x install.sh
sudo ./install.sh

# Install Ollama and a model
curl -fsSL https://ollama.com/install.sh | sh
sleep 5  # Wait for service to start
ollama pull tinyllama

# Set your token (replace with your actual token from dashboard)
sudo gpu-connect-token gpc_your_token_here

# Start the service
sudo systemctl start gpu-connect-agent
sudo systemctl enable gpu-connect-agent

# Check status
sudo systemctl status gpu-connect-agent

# View logs
journalctl -u gpu-connect-agent -f
```

### Managing the Agent on Linux

| Command | Description |
|---------|-------------|
| `sudo systemctl start gpu-connect-agent` | Start the agent |
| `sudo systemctl stop gpu-connect-agent` | Stop the agent |
| `sudo systemctl status gpu-connect-agent` | Check if running |
| `sudo systemctl restart gpu-connect-agent` | Restart the agent |
| `sudo gpu-connect-token <token>` | Update your agent token |
| `journalctl -u gpu-connect-agent -f` | View live logs |
| `sudo ./uninstall.sh` | Uninstall the agent |

### Troubleshooting on Linux

**Agent won't start:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check system logs
journalctl -u gpu-connect-agent -n 20 -p err
```

**Token rejected:**
```bash
# Generate a new token from dashboard, then:
sudo gpu-connect-token gpc_new_token
sudo systemctl restart gpu-connect-agent
```

**Ollama models not found:**
```bash
# Ensure Ollama service is running
sudo systemctl status ollama
# or on some systems:
systemctl status ollama
```

---

## macOS

### Prerequisites

- **macOS 12 (Monterey) or later**
- **Python 3.9+** (pre-installed, or `brew install python3`)
- **Ollama** (for local inference with Metal GPU acceleration on Apple Silicon)
- **Internet connection**

### Installation Steps

#### Step 1: Download the macOS Agent Package

Visit [gpu-connect.vercel.app](https://gpu-connect.vercel.app) and click **"macOS"** under downloads, or:

```bash
curl -O https://gpu-connect.vercel.app/downloads/gpu-connect-agent-macos.zip
```

#### Step 2: Extract and Install

```bash
# Extract the archive
unzip gpu-connect-agent-macos.zip -d gpu-connect-agent

# Navigate to directory
cd gpu-connect-agent

# Make scripts executable
chmod +x install.sh uninstall.sh

# Run the installer
./install.sh
```

The installer will:
- Create a virtual environment at `~/.gpu-connect-agent/`
- Install a macOS LaunchAgent for auto-start on login
- Create helper commands in `/usr/local/bin`

#### Step 3: Install Ollama

**Option A: Homebrew (Recommended)**

```bash
brew install ollama
ollama pull tinyllama
```

**Option B: Download directly**

Visit [ollama.com/download/mac](https://ollama.com/download/mac) and install the .dmg file.

Then:

```bash
ollama pull tinyllama
```

**Performance Note:** On Apple Silicon Macs (M1/M2/M3/M4), Ollama uses Metal GPU acceleration for fast inference.

#### Step 4: Generate Your Agent Token

1. Go to [gpu-connect.vercel.app](https://gpu-connect.vercel.app)
2. Log in to your dashboard
3. Go to **Provider** tab
4. Click **Generate Agent Token**
5. Copy the token (starts with `gpc_`)

#### Step 5: Set Your Token

```bash
gpu-connect-token gpc_your_token_here
```

#### Step 6: Start the Agent

```bash
# Start immediately
gpu-connect-start

# The agent will auto-start on next login via LaunchAgent
```

#### Step 7: Monitor Logs

```bash
# View logs
tail -f ~/.gpu-connect-agent/agent.log

# View error logs
tail -f ~/.gpu-connect-agent/agent.err.log
```

### Managing the Agent on macOS

| Command | Description |
|---------|-------------|
| `gpu-connect-start` | Start the agent |
| `gpu-connect-stop` | Stop the agent |
| `gpu-connect-status` | Check if running |
| `gpu-connect-token <token>` | Update your agent token |
| `tail -f ~/.gpu-connect-agent/agent.log` | View live logs |
| `./uninstall.sh` | Uninstall the agent |

### Quick Install (Copy-Paste All at Once)

```bash
# Download and install
curl -O https://gpu-connect.vercel.app/downloads/gpu-connect-agent-macos.zip
unzip gpu-connect-agent-macos.zip -d gpu-connect-agent
cd gpu-connect-agent
chmod +x install.sh
./install.sh

# Install Ollama via Homebrew
brew install ollama
ollama pull tinyllama

# Set your token (replace with token from dashboard)
gpu-connect-token gpc_your_token_here

# Start the agent
gpu-connect-start

# View logs
tail -f ~/.gpu-connect-agent/agent.log
```

### Troubleshooting on macOS

**Agent won't start:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check logs
tail -f ~/.gpu-connect-agent/agent.err.log
```

**Ollama not found:**
```bash
# Install via Homebrew
brew install ollama

# Or download from https://ollama.com/download/mac
```

**Permission denied installing:**
```bash
# Use sudo if necessary
sudo ./install.sh
```

---

## Getting Your Agent Token

All platforms require an agent token to authenticate with the GPU Connect network:

1. Go to **[gpu-connect.vercel.app](https://gpu-connect.vercel.app)**
2. **Log in** or create an account
3. Go to the **Dashboard** → **Provider** tab
4. Click **"Generate Agent Token"**
5. A token starting with `gpc_` will appear — **copy it**
6. Follow the platform-specific step to set the token

⚠️ **Security Note**: Tokens are shown only once. If you lose it, generate a new one.

---

## Next Steps: Earn Credits

Once your agent is running:

1. Your node appears in the **Marketplace**
2. Consumers can submit jobs to your models
3. Each completed job earns you credits ($0.80/job)
4. Track earnings in the **Provider Dashboard**

Monitor your nodes:
- **Windows**: Just run the agent, check the window for status
- **Linux/Pi**: `journalctl -u gpu-connect-agent -f` or check Dashboard
- **macOS**: `tail -f ~/.gpu-connect-agent/agent.log` or check Dashboard

---

## Support

For issues, check:
- The agent logs (commands above)
- [GitHub Issues](https://github.com/Himesh-29/GPUConnect/issues)
- Dashboard → Provider tab for node status

Happy computing! 🚀
