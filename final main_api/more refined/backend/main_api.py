import os
import shutil
import uuid
import subprocess
import time
import platform
import re
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path

app = FastAPI()

# Store job status and logs
RUN_STATUS = {}

BASE_DIR = Path(__file__).parent.resolve()
MODELS = {
    "clip": BASE_DIR / "babappa_clip_py" / "babappa_clip.py",
    "clipgard": BASE_DIR / "babappa_clipgard_py" / "babappa_clipgard.py",
    "normal": BASE_DIR / "babappa_normal_py" / "babappa_normal.py",
}

ALLOWED_FILES = {'.py', '.ctl'}

# Minimal step-detection patterns (edit or extend as needed)
STEP_PATTERNS = [
    # Matches: "STEP 1", "step2", etc. Captures numeric step id
    (re.compile(r'\bSTEP\s*[:\-]?\s*(\d+)\b', re.I), lambda m: {"type": "step", "id": int(m.group(1))}),
    # Matches lines like "PRANK finished" or "codeml finished"
    (re.compile(r'\b(prank|codeml)\b.*\b(finished|completed|done)\b', re.I), lambda m: {"type": "tool_done", "tool": m.group(1).lower()}),
    # Generic finished/completed/done lines
    (re.compile(r'\b(finished|completed|done)\b', re.I), lambda m: {"type": "completed"}),
    # Errors
    (re.compile(r'\bERROR\b', re.I), lambda m: {"type": "error"}),
]

def windows_to_wsl_path(p: str) -> Path:
    r"""Convert Windows path (C:\Users\...) to WSL path (/mnt/c/Users/...)."""
    p = p.strip('"')
    if platform.system() == "Linux" and ':' in p:
        drive, rest = p.split(':', 1)
        p = f"/mnt/{drive.lower()}{rest.replace('\\\\', '/').replace('\\', '/')}"
    return Path(p).resolve()

def wsl_to_windows_path(p: Path) -> Path:
    r"""Convert WSL path (/mnt/c/...) to Windows path (C:\...)."""
    p = p.resolve()
    if p.parts[0] == '/' and len(p.parts) > 2 and p.parts[1] == 'mnt':
        drive = p.parts[2].upper()
        rest = Path(*p.parts[3:])
        return Path(f"{drive}:\\") / rest
    return p

def move_generated_subfolders(model_folder: Path, destination: Path):
    """Move all subfolders created during the run from model_folder to destination."""
    destination.mkdir(parents=True, exist_ok=True)
    for item in list(model_folder.iterdir()):
        if item.is_dir():
            shutil.move(str(item), str(destination / item.name))

def clean_model_folder(model_folder: Path):
    """Ensure only .py and .ctl files remain in the model folder."""
    for item in model_folder.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        elif item.suffix not in ALLOWED_FILES:
            item.unlink()

@app.post("/run")
async def run_model(
    model: str = Form(...),
    output_folder: str = Form(...),
    fasta_file: UploadFile = File(...),
):
    if model not in MODELS:
        return JSONResponse(status_code=400, content={"status": "failed", "logs": ["Invalid model name"]})

    job_id = str(uuid.uuid4())
    RUN_STATUS[job_id] = {
        "status": "running",
        "logs": [f"Starting {model} run..."],
        "model": model,  # store model so stream_logs can find logs folder
    }

    # Always store as WSL path
    output_folder = windows_to_wsl_path(output_folder)
    model_path = MODELS[model]
    model_folder = model_path.parent

    # Save uploaded fasta file to model folder
    fasta_path = model_folder / fasta_file.filename
    with open(fasta_path, "wb") as f:
        f.write(await fasta_file.read())
    RUN_STATUS[job_id]["logs"].append(f"Copied {fasta_file.filename} to {model_folder.name}")

    def run_script():
        try:
            process = subprocess.Popen(
                ["python3", str(model_path), str(fasta_path)],
                cwd=str(model_folder),
                stdout=subprocess.DEVNULL,  # scripts are expected to write their own log files
                stderr=subprocess.STDOUT,
                text=True,
            )
            process.wait()

            if process.returncode != 0:
                RUN_STATUS[job_id]["status"] = "failed"
                RUN_STATUS[job_id]["logs"].append("Run failed.")
            else:
                # final_output_folder must remain a WSL path
                final_output_folder = output_folder / model / job_id
                final_output_folder.mkdir(parents=True, exist_ok=True)

                # Move results into correct WSL path
                move_generated_subfolders(model_folder, final_output_folder)

                # Clean up model folder
                if fasta_path.exists():
                    fasta_path.unlink()
                clean_model_folder(model_folder)

                # For logging/user-facing message only
                try:
                    final_output_folder_win = wsl_to_windows_path(final_output_folder)
                except Exception:
                    final_output_folder_win = final_output_folder

                RUN_STATUS[job_id]["status"] = "finished"
                RUN_STATUS[job_id]["logs"].append(
                    f"Run finished. Results moved to {final_output_folder_win}"
                )
        except Exception as e:
            RUN_STATUS[job_id]["status"] = "failed"
            RUN_STATUS[job_id]["logs"].append(f"ERROR: {str(e)}")

    import threading
    thread = threading.Thread(target=run_script)
    thread.start()

    return {"status": "running", "job_id": job_id}

@app.get("/status/{job_id}")
def status(job_id: str):
    if job_id not in RUN_STATUS:
        return JSONResponse(status_code=404, content={"status": "failed", "logs": ["Job ID not found"]})
    return RUN_STATUS[job_id]

@app.get("/stream/{job_id}")
def stream_logs(job_id: str):
    """
    Stream log lines (SSE) in real time for the job.
    - Dynamically picks up new *.log files in the model's logs folder.
    - Tails each file from the last read position and yields each new line immediately.
    - Mirrors each yielded line into RUN_STATUS[job_id]['logs'] so the status endpoint shows progress.
    - Detects step/tool completion lines and writes structured entries into RUN_STATUS[job_id]['steps'] and ['latest_step'].
    """
    if job_id not in RUN_STATUS:
        return JSONResponse(status_code=404, content={"status": "failed", "logs": ["Job ID not found"]})

    model = RUN_STATUS[job_id].get("model")
    if not model or model not in MODELS:
        return JSONResponse(status_code=400, content={"status": "failed", "logs": ["Unknown model for job"]})

    # Logs directory is inside the model’s folder
    logs_dir = MODELS[model].parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    def event_generator():
        file_positions = {}  # Path -> last read byte offset
        # initial scan
        for f in sorted(logs_dir.glob("*.log")):
            file_positions[f] = 0

        while True:
            # Re-scan to pick up new log files created after streaming started
            for f in sorted(logs_dir.glob("*.log")):
                if f not in file_positions:
                    file_positions[f] = 0

            # Tail each file from last known position
            for log_file in list(file_positions.keys()):
                try:
                    if not log_file.exists():
                        continue
                    with open(log_file, "r", encoding="utf-8", errors="replace") as fh:
                        fh.seek(file_positions[log_file])
                        while True:
                            line = fh.readline()
                            if not line:
                                break
                            # Strip trailing newline but keep content
                            content = line.rstrip("\n").rstrip("\r")
                            sse_line = f"data: {log_file.name}: {content}\n\n"
                            # Yield to SSE client
                            yield sse_line
                            # Also append to run status logs (keeps status endpoint in sync)
                            RUN_STATUS[job_id]["logs"].append(f"{log_file.name}: {content}")

                            # --- Minimal step detection: check patterns and update RUN_STATUS ---
                            for pattern, handler in STEP_PATTERNS:
                                m = pattern.search(content)
                                if m:
                                    info = handler(m)
                                    # store structured step events in 'steps' list and update latest_step
                                    RUN_STATUS[job_id].setdefault("steps", []).append({"line": content, **info})
                                    RUN_STATUS[job_id]["latest_step"] = {"line": content, **info}
                                    # exit pattern loop on first match (avoid duplicate matches)
                                    break
                            # --- end step detection ---

                        # update last read position
                        file_positions[log_file] = fh.tell()
                except Exception as e:
                    # If a single file fails, report and continue (don't break streaming)
                    err_msg = f"ERROR reading {log_file.name}: {str(e)}"
                    yield f"data: {err_msg}\n\n"
                    RUN_STATUS[job_id]["logs"].append(err_msg)

            # If finished or failed, flush any remaining content then stop
            if RUN_STATUS[job_id]["status"] in ("finished", "failed"):
                for log_file in list(file_positions.keys()):
                    try:
                        if not log_file.exists():
                            continue
                        with open(log_file, "r", encoding="utf-8", errors="replace") as fh:
                            fh.seek(file_positions[log_file])
                            for line in fh:
                                content = line.rstrip("\n").rstrip("\r")
                                yield f"data: {log_file.name}: {content}\n\n"
                                RUN_STATUS[job_id]["logs"].append(f"{log_file.name}: {content}")
                                # also try detecting steps on final flush
                                for pattern, handler in STEP_PATTERNS:
                                    m = pattern.search(content)
                                    if m:
                                        info = handler(m)
                                        RUN_STATUS[job_id].setdefault("steps", []).append({"line": content, **info})
                                        RUN_STATUS[job_id]["latest_step"] = {"line": content, **info}
                                        break
                    except Exception:
                        pass
                # final status notification
                yield f"data: __status__: {RUN_STATUS[job_id]['status']}\n\n"
                break

            # Heartbeat comment to keep connections alive (SSE comment)
            yield ": heartbeat\n\n"
            time.sleep(0.2)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
