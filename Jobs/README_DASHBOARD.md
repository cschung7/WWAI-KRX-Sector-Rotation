# Dashboard Management Scripts

This directory contains shell scripts to manage the Investment Focus Dashboard.

## Available Scripts

### 1. `start_dashboard.sh` - Start the Dashboard Server

Starts the FastAPI backend server for the dashboard.

**Usage:**
```bash
./start_dashboard.sh [options]
```

**Options:**
- `--port PORT` - Set the port number (default: 8000)
- `--host HOST` - Set the host address (default: 0.0.0.0)
- `--reload` - Enable auto-reload on code changes (default: enabled)
- `--no-reload` - Disable auto-reload
- `--help` - Show help message

**Examples:**
```bash
# Start on default port 8000
./start_dashboard.sh

# Start on custom port
./start_dashboard.sh --port 8080

# Start without auto-reload
./start_dashboard.sh --no-reload
```

**What it does:**
1. Checks if backend directory exists
2. Verifies Python and dependencies are installed
3. Installs requirements if needed
4. Checks if port is already in use
5. Starts the FastAPI server with uvicorn

---

### 2. `stop_dashboard.sh` - Stop the Dashboard Server

Stops the running dashboard server.

**Usage:**
```bash
./stop_dashboard.sh [port]
```

**Arguments:**
- `port` - Port number (default: 8000)

**Examples:**
```bash
# Stop server on default port 8000
./stop_dashboard.sh

# Stop server on custom port
./stop_dashboard.sh 8080
```

---

### 3. `check_dashboard.sh` - Check Dashboard Status

Checks if the dashboard server is running and healthy.

**Usage:**
```bash
./check_dashboard.sh [port]
```

**Arguments:**
- `port` - Port number (default: 8000)

**Examples:**
```bash
# Check default port
./check_dashboard.sh

# Check custom port
./check_dashboard.sh 8080
```

**What it checks:**
- If server process is running
- Health endpoint response
- Provides dashboard URLs

---

## Quick Start

### First Time Setup

1. **Make scripts executable:**
   ```bash
   chmod +x start_dashboard.sh stop_dashboard.sh check_dashboard.sh
   ```

2. **Start the dashboard:**
   ```bash
   ./start_dashboard.sh
   ```

3. **Open the dashboard:**
   - Dashboard: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: Open `dashboard/frontend/index.html` in browser

### Daily Usage

1. **Check if running:**
   ```bash
   ./check_dashboard.sh
   ```

2. **Start if not running:**
   ```bash
   ./start_dashboard.sh
   ```

3. **Stop when done:**
   ```bash
   ./stop_dashboard.sh
   ```

---

## Troubleshooting

### Port Already in Use

If you see "Port 8000 is already in use":

```bash
# Option 1: Stop the existing server
./stop_dashboard.sh

# Option 2: Use a different port
./start_dashboard.sh --port 8080
```

### Dependencies Not Installed

The script will automatically install dependencies if `uvicorn` is not found. If you encounter issues:

```bash
cd ../dashboard/backend
pip install -r requirements.txt
```

### Server Won't Start

1. Check Python version:
   ```bash
   python3 --version  # Should be 3.8+
   ```

2. Check if backend directory exists:
   ```bash
   ls -la ../dashboard/backend
   ```

3. Check backend logs for errors

---

## Integration with Weekly Analysis

You can integrate the dashboard with your weekly analysis workflow:

```bash
# After running weekly analysis
cd ../Jobs
./start_dashboard.sh

# Dashboard will show latest analysis results
```

---

## Production Deployment

For production, you may want to:

1. **Disable auto-reload:**
   ```bash
   ./start_dashboard.sh --no-reload
   ```

2. **Use a process manager** (systemd, supervisor, etc.)

3. **Set up reverse proxy** (nginx, Apache)

4. **Enable HTTPS**

5. **Add authentication**

---

## File Structure

```
Jobs/
├── start_dashboard.sh      # Start server script
├── stop_dashboard.sh       # Stop server script
├── check_dashboard.sh      # Status check script
└── README_DASHBOARD.md     # This file
```

