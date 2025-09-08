Babappa GUI v1.0

Author: Krishnendu Sinha
Institution: Jhargram Raj College
Email: dr.krishnendusinha@gmail.com

Version: 1.0
Release Date: September 2025

Babappa GUI is a graphical interface for the Babappa pipeline, enabling easy analysis without manually running Linux scripts. It runs on Windows 10/11 using WSL2 (Windows Subsystem for Linux v2).

-------------------------------------------------------------
System Requirements

- Windows 10 or 11 (64-bit)
- Minimum 8 GB RAM recommended
- WSL2 support (Windows Subsystem for Linux v2)
- ~4–5 GB free disk space for WSL distribution and Conda environment

-------------------------------------------------------------
Installation

1. Download the Installer
   Double-click the Babappa GUI installer (BabappaInstaller.exe) included in the distribution.

2. WSL2 Setup
   - The installer checks if WSL2 is installed.
   - If WSL2 is not found, run in PowerShell:
     wsl --install
   - Restart your computer if prompted.

3. Import Babappa WSL Environment
   - The installer imports a pre-packaged Ubuntu 22.04 distribution (babappa_clean.tar.xz) as 'Babappa'.
   - This environment includes Python, Conda, and all required packages.
   - No manual setup is required — everything is pre-configured.

4. Creating Desktop Shortcut
   - The installer creates a desktop shortcut and Start Menu entry for Babappa GUI.
   - Double-click to launch the GUI.

-------------------------------------------------------------
Launching Babappa GUI

1. Double-click the Babappa GUI shortcut.
2. The GUI connects automatically to the WSL environment in the background.
3. You can now run analyses directly from the GUI.

-------------------------------------------------------------
File Structure (Inside Installer)

- babappa_clean.tar.xz — Pre-packaged WSL Ubuntu distribution with Conda environment
- babappa_env.yml — Conda environment file (backup)
- babappa_gui.exe — Executable of Babappa GUI
- main_api.py — Backend API for GUI
- dist/ — PyInstaller build folder (optional)
- winvenv/ — Optional Python virtual environment (Windows)
- babappa_installer.iss — Inno Setup script for building installer

-------------------------------------------------------------
Troubleshooting

GUI Errors

- ModuleNotFoundError (PyQt6, requests, etc.)
  All Python dependencies are included in the Conda environment. Ensure WSL2 and Babappa distribution are properly installed.

- Backend API fails
  Make sure Babappa WSL environment is registered and Conda is activated:
    wsl -d Babappa
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate babappa
    python3 main_api.py

- GUI does not launch from desktop shortcut
  Ensure WSL2 is installed and Babappa distribution exists:
    wsl --list --verbose
  You should see 'Babappa' with version 2.

Reinstallation

- To reset the Babappa WSL environment:
    wsl --unregister Babappa
    wsl --import Babappa <InstallFolder> <PathToTarball> --version 2

-------------------------------------------------------------
Usage Notes

- This is Babappa GUI v1.0, while the pipeline is version 2.0.
- All analyses are executed inside WSL for compatibility.
- No Linux commands are required — everything is GUI-driven.

-------------------------------------------------------------
Contact

Developer: Krishnendu Sinha
Institution: Jhargram Raj College
Email: dr.krishnendusinha@gmail.com
