import sys

# Force UTF-8 output on Windows terminals that default to cp1252/cp1254.
# This must run before any print() call to prevent UnicodeEncodeError.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import socket
import subprocess
from pathlib import Path


def find_free_port(start_port: int = 8001) -> int:
    """Finds the first available TCP port starting from start_port."""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1


def setup_environment() -> None:
    """Sets up the virtual environment and required configurations automatically."""
    print("[INIT] Initiating SaaS AI Engine Bootstrapper...")

    # 1. Environment Variables Configuration
    env_path = Path('.env')
    if not env_path.exists():
        print("[WARN] .env file is missing. Generating automatically...")
        gemini_key = input("Please enter your Google Gemini API Key: ")
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(f"GEMINI_API_KEY={gemini_key}\n")
            f.write("SAAS_API_KEY=demo-tenant-key-123\n")
        print("[OK] .env file created successfully.")

    # 2. Virtual Environment Initialization
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print("[WARN] Virtual environment not found. Creating 'venv'...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])

        # Install dependencies.
        print("[PKG] Installing required dependencies (this may take a moment)...")
        pip_cmd = (
            os.path.join(venv_dir, "Scripts", "pip.exe")
            if os.name == "nt"
            else os.path.join(venv_dir, "bin", "pip")
        )
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"])
        print("[OK] All dependencies installed successfully.")


def start_server() -> None:
    """Boots up the FastAPI application on the first available port."""
    # Honour $PORT if set by master_launcher.py, otherwise discover one.
    port_env = os.environ.get("PORT")
    port = int(port_env) if port_env else find_free_port()

    print(f"[READY] Autonomous AI Brain is starting on port {port}...")

    uvicorn_cmd = (
        os.path.join("venv", "Scripts", "uvicorn.exe")
        if os.name == "nt"
        else os.path.join("venv", "bin", "uvicorn")
    )

    # Fall back to system uvicorn if the venv binary does not exist yet.
    if not os.path.exists(uvicorn_cmd):
        uvicorn_cmd = "uvicorn"

    try:
        subprocess.run(
            [uvicorn_cmd, "main:app", "--host", "0.0.0.0", "--port", str(port), "--reload"]
        )
    except KeyboardInterrupt:
        print("\n[STOP] Server shut down gracefully.")


if __name__ == "__main__":
    setup_environment()
    start_server()