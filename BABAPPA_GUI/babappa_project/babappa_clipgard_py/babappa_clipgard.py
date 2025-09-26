#!/usr/bin/env python3
import os
import subprocess
import time

# Master runner script for babappa pipeline (Python version)

MASTER_LOG = "master_log.txt"
with open(MASTER_LOG, "w") as f:
    f.write(f"=================== Master run started: {time.ctime()} ===================\n")

def log(msg):
    with open(MASTER_LOG, "a") as f:
        f.write(msg + "\n")
    print(msg)

def run_script(script_name):
    log("--------------------------------------------------")
    log(f"Running {script_name} at {time.ctime()}")
    start_time = time.time()

    if not os.path.isfile(script_name):
        log(f"Error: {script_name} not found!")
        exit(1)

    proc = subprocess.Popen(["python3", script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        log(line.strip())
    proc.wait()

    elapsed = int(time.time() - start_time)
    log(f"Completed {script_name} at {time.ctime()} (Elapsed time: {elapsed}s)\n")

# Step 1: Run script0.py and script0.5.py
run_script("script0.py")
run_script("script0.5.py")

# Step 2: Run script1.py to script8.py sequentially
for i in range(1, 9):
    run_script(f"script{i}.py")

log(f"=================== Master run completed: {time.ctime()} ===================")
