import os
import shutil
import uuid
import subprocess
import time
import platform
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

def windows_to_wsl_path(p: str) -> Path:
    r"""Convert Windows path (C:\Users\...) to WSL path (/mnt/c/Users/...)."""
    p = p.strip('"')
    if platform.system() == "Linux" and ':' in p:
        drive, rest = p.split(':', 1)
        p = f"/mnt/{drive.lower()}{rest.replace('\\\\','/').replace('\\','/')}"
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
                stdout=subprocess.DEVNULL,  # Ignore stdout
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
    if job_id not in RUN_STATUS:
        return JSONResponse(status_code=404, content={"status": "failed", "logs": ["Job ID not found"]})

    model = RUN_STATUS[job_id].get("model")
    if not model or model not in MODELS:
        return JSONResponse(status_code=400, content={"status": "failed", "logs": ["Unknown model for job"]})

    # Logs directory is inside the model’s folder
    logs_dir = MODELS[model].parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    def event_generator():
        file_pointers = {f: 0 for f in logs_dir.glob("script*.log")}
        while True:
            for log_file, pos in list(file_pointers.items()):
                if not log_file.exists():
                    continue
                with open(log_file, "r") as f:
                    f.seek(pos)
                    for line in f:
                        yield f"data: {log_file.name}: {line.strip()}\n\n"
                    file_pointers[log_file] = f.tell()
            if RUN_STATUS[job_id]["status"] in ("finished", "failed"):
                # Flush remaining lines
                for log_file, pos in list(file_pointers.items()):
                    if not log_file.exists():
                        continue
                    with open(log_file, "r") as f:
                        f.seek(pos)
                        for line in f:
                            yield f"data: {log_file.name}: {line.strip()}\n\n"
                break
            time.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
