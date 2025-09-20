#!/usr/bin/env bash
set -euo pipefail

# Current working directory is {app}/dist
APP_DIR="$(pwd)"
ROOT_DIR="$(dirname "$APP_DIR")"

# Paths to assets (one level up from dist)
ENV_TAR="$ROOT_DIR/babappa_env.tar.gz"
MINICONDA_INSTALLER="$ROOT_DIR/Miniconda3-latest-Linux-x86_64.sh"
PROJECT_SRC="$ROOT_DIR/babappa_project"

# WSL home destinations
ENV_DIR="$HOME/babappa_env"
PROJECT_DIR="$HOME/babappa_project"
LOG_FILE="$HOME/babappa_uvicorn.log"
PID_FILE="$HOME/babappa_uvicorn.pid"

echo "[INFO] start_babappa.sh running from $APP_DIR"
echo "[INFO] Using tarball: $ENV_TAR"
echo "[INFO] Using project: $PROJECT_SRC"

# 1. Ensure Miniconda
if ! command -v conda >/dev/null 2>&1; then
    if [ ! -d "$HOME/miniconda3" ]; then
        echo "[INFO] Installing Miniconda..."
        bash "$MINICONDA_INSTALLER" -b -p "$HOME/miniconda3"
        "$HOME/miniconda3/bin/conda" init bash || true
    else
        echo "[INFO] Miniconda already exists at $HOME/miniconda3"
    fi
else
    echo "[INFO] conda already available"
fi

# 2. Restore environment
if [ ! -f "$ENV_TAR" ]; then
    echo "[ERROR] Environment tarball not found at $ENV_TAR"
    exit 1
fi

echo "[INFO] Restoring environment..."
rm -rf "$ENV_DIR"
mkdir -p "$ENV_DIR"
tar -xzf "$ENV_TAR" -C "$ENV_DIR"

if [ -x "$ENV_DIR/bin/conda-unpack" ]; then
    echo "[INFO] Running conda-unpack..."
    "$ENV_DIR/bin/conda-unpack" || true
fi

# 3. Sync project
if [ ! -d "$PROJECT_SRC" ]; then
    echo "[ERROR] Project folder missing: $PROJECT_SRC"
    exit 1
fi

echo "[INFO] Syncing project files..."
rsync -a --delete "$PROJECT_SRC"/ "$PROJECT_DIR"/

# Ensure write permissions
echo "[INFO] Fixing permissions on project directory..."
chmod -R u+rwX "$PROJECT_DIR"

# 4. Kill any old API
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[INFO] Killing old API process $OLD_PID"
        kill "$OLD_PID" || true
    fi
fi

# Also ensure port 8000 is free
if lsof -i :8000 >/dev/null 2>&1; then
    echo "[INFO] Port 8000 already in use, killing process on port 8000"
    fuser -k 8000/tcp || true
fi

# 5. Start uvicorn
cd "$PROJECT_DIR"

if [ ! -f "babappa_api.py" ]; then
    echo "[ERROR] babappa_api.py not found in $PROJECT_DIR"
    exit 1
fi

echo "[INFO] Starting API server..."
nohup "$ENV_DIR/bin/python" -m uvicorn babappa_api:app \
    --host 127.0.0.1 --port 8000 \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"
echo "[INFO] Uvicorn started with PID $PID"
