import os
import shutil
import uuid
import subprocess
import time
import platform
import re
import sys
import threading
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path

app = FastAPI()
RUN_STATUS = {}

@app.get("/")
def health_check():
    return {"status": "ok"}


BASE_DIR = Path(__file__).parent.resolve()
MODELS = {
    "clip": BASE_DIR / "babappa_clip_py" / "babappa_clip.py",
    "clipgard": BASE_DIR / "babappa_clipgard_py" / "babappa_clipgard.py",
    "normal": BASE_DIR / "babappa_normal_py" / "babappa_normal.py",
}
ALLOWED_FILES = {".py", ".ctl"}

STEP_PATTERNS = [
    (re.compile(r"\bSTEP\s*[:\-]?\s*(\d+)\b", re.I),
     lambda m: {"type": "step", "id": int(m.group(1))}),
    (re.compile(r"\b(prank|codeml)\b.*\b(finished|completed|done)\b", re.I),
     lambda m: {"type": "tool_done", "tool": m.group(1).lower()}),
    (re.compile(r"\b(finished|completed|done)\b", re.I),
     lambda m: {"type": "completed"}),
    (re.compile(r"\bERROR\b", re.I),
     lambda m: {"type": "error"}),
]


def windows_to_wsl_path(p: str) -> Path:
    p = p.strip('"')
    if platform.system() == "Linux" and ":" in p:
        drive, rest = p.split(":", 1)
        rest = rest.replace("\\", "/").lstrip("/")
        p = f"/mnt/{drive.lower()}/{rest}"
    return Path(p).resolve()


def wsl_to_windows_path(p: Path) -> Path:
    p = p.resolve()
    if p.parts[0] == "/" and len(p.parts) > 2 and p.parts[1] == "mnt":
        drive = p.parts[2].upper()
        rest = Path(*p.parts[3:])
        return Path(f"{drive}:\\") / rest
    return p


def move_generated_subfolders(model_folder: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for item in list(model_folder.iterdir()):
        if item.is_dir():
            shutil.move(str(item), str(destination / item.name))


def clean_model_folder(model_folder: Path):
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
        return JSONResponse(
            status_code=400,
            content={"status": "failed", "logs": ["Invalid model name"]}
        )

    job_id = str(uuid.uuid4())
    RUN_STATUS[job_id] = {"status": "running", "logs": [], "model": model}

    output_folder = windows_to_wsl_path(output_folder)
    model_path = MODELS[model]
    model_folder = model_path.parent
    logs_dir = model_folder / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    job_log = logs_dir / f"{job_id}.log"

    fasta_path = model_folder / fasta_file.filename
    with open(fasta_path, "wb") as f:
        f.write(await fasta_file.read())

    def run_script():
        try:
            with open(job_log, "a", encoding="utf-8") as lf:
                lf.write(f"--- Job {job_id} started for model {model} ---\n")

            with open(job_log, "a", encoding="utf-8") as lf:
                process = subprocess.Popen(
                    [sys.executable, str(model_path)],   # ✅ no fasta arg
                    cwd=str(model_folder),
                    stdout=lf,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                process.wait()
                rc = process.returncode
                lf.write(f"\n--- Driver exited with code {rc} ---\n")

            if rc != 0:
                RUN_STATUS[job_id]["status"] = "failed"
                with open(job_log, "a", encoding="utf-8") as lf:
                    lf.write("\n--- Process exited with non-zero code ---\n")
                return

            # ✅ Post-processing
            try:
                final_output_folder = output_folder / model / job_id
                final_output_folder.mkdir(parents=True, exist_ok=True)

                try:
                    move_generated_subfolders(model_folder, final_output_folder)
                except Exception as e:
                    with open(job_log, "a", encoding="utf-8") as lf:
                        lf.write(f"\nWARNING: Failed to move subfolders → {e}\n")

                if fasta_path.exists():
                    try:
                        fasta_path.unlink()
                    except Exception as e:
                        with open(job_log, "a", encoding="utf-8") as lf:
                            lf.write(f"\nWARNING: Could not delete fasta → {e}\n")

                try:
                    clean_model_folder(model_folder)
                except Exception as e:
                    with open(job_log, "a", encoding="utf-8") as lf:
                        lf.write(f"\nWARNING: Cleanup failed → {e}\n")

                try:
                    final_output_folder_win = wsl_to_windows_path(final_output_folder)
                except Exception:
                    final_output_folder_win = final_output_folder

                RUN_STATUS[job_id]["status"] = "finished"
                with open(job_log, "a", encoding="utf-8") as lf:
                    lf.write(
                        f"\nRun finished. Results moved to {final_output_folder_win}\n"
                    )

            except Exception as e:
                RUN_STATUS[job_id]["status"] = "failed"
                with open(job_log, "a", encoding="utf-8") as lf:
                    lf.write(f"\nERROR in post-processing: {e}\n")

        except Exception as e:
            RUN_STATUS[job_id]["status"] = "failed"
            with open(job_log, "a", encoding="utf-8") as lf:
                lf.write(f"\nERROR: {e}\n")

    threading.Thread(target=run_script, daemon=True).start()
    return {"status": "running", "job_id": job_id}


@app.get("/status/{job_id}")
def status(job_id: str):
    if job_id not in RUN_STATUS:
        return JSONResponse(
            status_code=404,
            content={"status": "failed", "logs": ["Job ID not found"]}
        )
    return RUN_STATUS[job_id]


@app.get("/stream/{job_id}")
def stream_logs(job_id: str):
    if job_id not in RUN_STATUS:
        return JSONResponse(
            status_code=404,
            content={"status": "failed", "logs": ["Job ID not found"]}
        )

    model = RUN_STATUS[job_id].get("model")
    logs_dir = MODELS[model].parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    def event_generator():
        file_positions = {}  # track file read offsets

        while True:
            # Pick up new log files dynamically
            for log_file in sorted(logs_dir.glob("*.log")):
                if log_file not in file_positions:
                    file_positions[log_file] = 0

            # Stream new lines from each log file
            for log_file, pos in list(file_positions.items()):
                try:
                    if not log_file.exists():
                        continue
                    with open(log_file, "r", encoding="utf-8", errors="replace") as fh:
                        fh.seek(pos)
                        for line in fh:
                            content = line.rstrip("\r\n")
                            # Prefix with filename so GUI knows source
                            yield f"data: {log_file.name}: {content}\n\n"
                            RUN_STATUS[job_id]["logs"].append(f"{log_file.name}: {content}")

                            # Step detection
                            for pattern, handler in STEP_PATTERNS:
                                m = pattern.search(content)
                                if m:
                                    info = handler(m)
                                    RUN_STATUS[job_id].setdefault("steps", []).append(
                                        {"line": content, **info}
                                    )
                                    RUN_STATUS[job_id]["latest_step"] = {"line": content, **info}
                                    break
                        file_positions[log_file] = fh.tell()
                except Exception as e:
                    err_msg = f"ERROR reading {log_file.name}: {e}"
                    yield f"data: {err_msg}\n\n"
                    RUN_STATUS[job_id]["logs"].append(err_msg)

            # End when job finishes
            if RUN_STATUS[job_id]["status"] in ("finished", "failed"):
                for log_file, pos in list(file_positions.items()):
                    try:
                        if not log_file.exists():
                            continue
                        with open(log_file, "r", encoding="utf-8", errors="replace") as fh:
                            fh.seek(pos)
                            for line in fh:
                                content = line.rstrip("\r\n")
                                yield f"data: {log_file.name}: {content}\n\n"
                                RUN_STATUS[job_id]["logs"].append(f"{log_file.name}: {content}")
                    except Exception:
                        pass
                #yield f"data: __status__: {RUN_STATUS[job_id]['status']}\n\n"
                break

            yield ": heartbeat\n\n"
            time.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



if __name__ == "__main__":
    import uvicorn
    print(">>> Starting Babappa API on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
