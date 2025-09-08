#!/usr/bin/env python3
"""
Babappa ClipGard Sequential Runner
Runs scripts sequentially in this order:
script0_clipgard.py → script0.5_clipgard.py → script1_clipgard.py → script1.5_clipgard.py → ... → script8_clipgard.py
"""

import subprocess
import sys
from pathlib import Path

# Base folder where this script resides
BASE_DIR = Path(__file__).resolve().parent

# List of scripts in order
scripts = [
    "script0_clipgard.py",
    "script0.5_clipgard.py",
    "script1_clipgard.py",
    "script1.5_clipgard.py",
    "script2_clipgard.py",
    "script3_clipgard.py",
    "script4_clipgard.py",
    "script5_clipgard.py",
    "script6_clipgard.py",
    "script7_clipgard.py",
    "script8_clipgard.py"
]

# Ensure logs directory exists
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

def run_script(script_name: str):
    script_path = BASE_DIR / script_name
    log_file = logs_dir / f"{script_name.replace('.py', '')}.log"

    print(f"▶ Running {script_name}...")

    with log_file.open("w") as f:
        process = subprocess.run(
            [sys.executable, str(script_path)],
            stdout=f,
            stderr=subprocess.STDOUT
        )

    if process.returncode != 0:
        print(f"❌ {script_name} failed. Check log: {log_file}")
        return False
    else:
        print(f"✅ {script_name} completed. Log: {log_file}")
        return True

def main():
    for script in scripts:
        success = run_script(script)
        if not success:
            print("Pipeline stopped due to error.")
            break

if __name__ == "__main__":
    main()
