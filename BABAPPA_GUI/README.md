# BABAPPA — README  🔧✨📘

**Purpose:** a single, friendly, and robust README that combines installation, first-run, usage, results, troubleshooting, and developer/maintenance notes for the BABAPPA pipeline. 📝🌟🔍

---

# Quick start (3 steps) 🚀✅🎯

1. **Install** — run the provided Babappa installer (`babappa_installer_2.0.exe`) as Administrator and accept the defaults. The installer places files under `C:\Program Files (x86)\Babappa` (default).
2. **Launch** — double-click the **Babappa** shortcut (Start Menu or Desktop). The GUI will start and bring up a backend API inside WSL (Ubuntu-22.04).
3. **Run analysis** — choose a FASTA input, select an output folder, pick a pipeline (`clip`, `clipgard`, or `normal`) and click **Run**.

*If anything fails, see the Troubleshooting section below — copy/paste commands are provided.* 🛠️📋🔎

---

# Requirements  🖥️⚙️📥

- Windows 10/11 (64-bit)
- **WSL 2** with **Ubuntu-22.04** installed and initialized
- \~5–10 GB free disk space (for environment + results)
- Optional but recommended: internet access for first-time Miniconda download if not packaged.

---

# What the installer / first run does  🧩🔁📦

On first run the GUI performs these steps automatically (this is expected behaviour): 🔄📌✨

- Installs **Miniconda** into the WSL Ubuntu-22.04 distro if not present.
- Restores the provided conda environment (`babappa_env`) from `babappa_env.tar.gz` or creates it from `babappa_env.yml`.
- Copies the backend project folder (`babappa_project`) into your WSL home as `~/babappa_project`.
- Starts the FastAPI/uvicorn backend (`babappa_api`) inside WSL and the GUI connects to it.

This may take 10–20 minutes on first run depending on your machine and whether files need to be downloaded. ⏳🧭📶

---

# Typical paths  📁🧭🔎

**Windows (user-facing results):** 📂✨🔍

```
C:\Users\<YourWindowsUsername>\Documents\out\
```

Inside `out/` you will see three top-level pipeline folders: `clip/`, `clipgard/`, and `normal/`. Each run creates a unique subfolder named with a UUID. 🗂️🆔📊

**WSL (internal runtime files):** 🐧🔧📄

```
~/babappa_project/              # copied project in WSL home
~/babappa_uvicorn.log           # API startup/runtime log
~/miniconda3/envs/babappa       # conda env (if created normally)
```

You can also view WSL files from Windows Explorer via the `\\wsl$\Ubuntu-22.04\home\<username>` path. 🪟🔗📁

---

# Results layout (what you will usually need)  🧾📚🔬

Each run folder (UUID) contains a consistent subfolder structure. Example (abridged): 🗄️🧷📁

```
out/
 ├─ clip/ | clipgard/ | normal/
 │   └─ <run-id>/
 │       ├─ BHanalysis/
 │       ├─ BHanalysis4sitemodel/
 │       ├─ codemlanalysis/
 │       ├─ codemloutput/
 │       ├─ foregroundbranch/
 │       ├─ iqtreeoutput/
 │       ├─ logs/
 │       ├─ msa/
 │       ├─ sitemodel/
 │       ├─ sitemodelanalysis/
 │       └─ treefiles/
```

**Key files to check for publication / reporting:** 📑🧾🔎

- `BHanalysis/LRT_results_lnL_np_values.xlsx` — LRT results & p-values.
- `BHanalysis4sitemodel/lrt_results.csv` — site-model LRT results.
- `codemlanalysis/lnL_np_values.csv` and `sitemodelanalysis/lnL_np_values.csv` — codeml summaries.
- `codemloutput/` — full PAML/Codeml outputs (`output.txt`, `rst`, `rub`, etc.).
- `iqtreeoutput/*.treefile` — phylogenetic trees (use these for figures/publication).
- `msa/*.fas` — alignments used for analysis.
- `logs/*.log` — one log per script step (these are the best place to begin debugging).

---

# How to run manually (advanced users)  🧑‍💻🛠️📡

Sometimes you might want to start or debug the API manually from WSL: 🖱️🔍🛠️

1. Open PowerShell and enter WSL:

```powershell
wsl
# now you are in Ubuntu-22.04 shell
```

2. Change to the installation folder inside the WSL-mounted Windows path and start the bundled script:

```bash
cd "/mnt/c/Program Files (x86)/Babappa"
bash start_babappa.sh
# or if you have the dist layout:
bash start_babappa.sh
```

3. To stop the API (or kill stale servers):

```bash
pkill -f "uvicorn babappa_api:app" || true
```

4. To inspect the backend log:

```bash
tail -n 100 ~/babappa_uvicorn.log
```

---

# Common problems & fixes (copy-paste commands) 🩺🛠️📋

### Problem: API did not start / GUI shows `API did not start` ⚠️🔍🚫

**Check:** Ensure WSL Ubuntu-22.04 exists and is default:

```powershell
wsl -l -v
```

If missing, install via PowerShell (Admin):

```powershell
wsl --install -d Ubuntu-22.04
```

Then re-run the GUI. 🔁✅📥

---

### Problem: `CondaToSNonInteractiveError: Terms of Service have not been accepted...` 📜❗🔐

Run these inside WSL to accept conda TOS for non-interactive installs:

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

---

### Problem: PermissionError when writing logs or results 🔐🧾🛠️

Fix permissions inside WSL on the copied project folder:

```bash
sudo chown -R $(whoami):$(whoami) ~/babappa_project
chmod -R u+w ~/babappa_project
```

Then re-run the GUI. ♻️🔧📂

---

### Problem: `uvicorn` or dependencies missing 📦⚠️🔧

Activate the environment and (re)install missing packages:

```bash
conda activate babappa_env
pip install uvicorn fastapi
```

---

### Problem: Old server still running / port in use 🔁🚫🔌

```bash
pkill -f "uvicorn babappa_api:app" || true
```

Then restart the GUI. 🔁🖥️🔄

---

### Problem: GUI shows `Internal Server Error` or silent failures ❗🧭🧰

- Inspect `~/babappa_uvicorn.log` for stack traces:

```bash
tail -n 200 ~/babappa_uvicorn.log > ~/api_error.log
# Attach api_error.log to support requests
```

- If errors indicate permission issues, see permissions fix above. 🔎🗂️🆘

---

# Reset / Uninstall (safe cleanup) ♻️🗑️🧽

**In WSL** (kills API, removes project and env):

```bash
pkill -f "uvicorn babappa_api:app" || true
rm -rf ~/babappa_project
rm -rf ~/miniconda3/envs/babappa_env
rm -f ~/babappa_uvicorn.log ~/babappa_uvicorn.pid
```

**In Windows** 🪟🧾🔚

- Use Control Panel → Add/Remove Programs → Uninstall Babappa, or:

```powershell
Remove-Item -Recurse -Force "C:\Program Files (x86)\Babappa"
```

---

# Developer / Maintainer notes 🧑‍🔧📦📝

**Project layout (source tree):** 📁🔍🧩

```
babappa_build/
├─ babappa_api.py
├─ babappa_project/
│  ├─ babappa_clip_py/
│  ├─ babappa_clipgard_py/
│  └─ babappa_normal_py/
├─ babappa_env.tar.gz
├─ Miniconda3-latest-Linux-x86_64.sh
├─ dist/
├─ babappa_installer.iss
├─ butterfly_icon.ico
└─ butterfly_icon.png
```

**Rebuild the GUI (PyInstaller)** 🛠️📦🔧

When you change `babappa_gui.py`, rebuild with:

```bash
pyinstaller --noconfirm --onefile --windowed \
  --icon=butterfly_icon.ico \
  --name=babappa_gui babappa_gui.py
```

Result: `dist/babappa_gui.exe`. 🧩📦✅

**Update Conda environment** 🔁📦🧪

1. Make changes in your dev env.
2. Pack it:

```bash
conda pack -n babappa_env -o babappa_env.tar.gz
```

3. Replace the `babappa_env.tar.gz` in the build folder before making a new installer.

**Build the installer** 🧩📥🛠️

- Use **Inno Setup Compiler** with `babappa_installer.iss` to create `babappa_installer_2.0.exe`.

**Release checklist (recommended):** ✅📋🔎

-

---

# How to collect useful debug information (what to attach when you ask for help) 🧾📤🔍

1. `wsl -l -v` output from PowerShell.
2. Last 200 lines of `~/babappa_uvicorn.log` (or the full `api_error.log`).
3. A screenshot of the GUI error or the GUI log pane.
4. A small sample input and the chosen pipeline (if reproducing a run issue).

Send these to the developer email (below) or attach to a support ticket. 📨🛠️📎

---

# Contact & support 📬👩‍💻📞

Developer: **Krishnendu Sinha**\
Email: [dr.krishnendusinha@gmail.com](mailto\:dr.krishnendusinha@gmail.com) ✉️📨📬

---

# Appendix — Common commands cheat-sheet 🧾⚡🔧

```
# Check WSL distros (PowerShell)
wsl -l -v

# Install Ubuntu 22.04 (PowerShell Admin)
wsl --install -d Ubuntu-22.04

# Start Babappa manually (WSL shell)
cd "/mnt/c/Program Files (x86)/Babappa"
bash start_babappa.sh

# View API log (WSL)
tail -n 100 ~/babappa_uvicorn.log

# Accept Conda TOS (WSL)
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Fix permissions (WSL)
sudo chown -R $(whoami):$(whoami) ~/babappa_project
chmod -R u+w ~/babappa_project

# Kill uvicorn if it's stuck (WSL)
pkill -f "uvicorn babappa_api:app" || true
```

---

