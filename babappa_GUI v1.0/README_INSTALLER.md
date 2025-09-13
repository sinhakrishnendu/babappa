Babappa Installer – Maintenance Guide
=====================================

This document explains how to build and maintain the Babappa standalone installer.

---------------------------------------------------------
1. Project Layout
---------------------------------------------------------

Your source tree should look like:

babappa_build/
├── babappa_api.py
├── babappa_project/
│   ├── babappa_clip_py/
│   ├── babappa_clipgard_py/
│   └── babappa_normal_py/
├── babappa_env.tar.gz
├── Miniconda3-latest-Linux-x86_64.sh
├── dist/
│   ├── babappa_gui.exe
│   └── start_babappa.sh
├── babappa_installer.iss
├── butterfly_icon.ico
└── butterfly_icon.png

---------------------------------------------------------
2. Rebuilding the GUI
---------------------------------------------------------

If you change babappa_gui.py:

    pyinstaller --noconfirm --onefile --windowed ^
      --icon=butterfly_icon.ico ^
      --name=babappa_gui babappa_gui.py

The result appears in dist/babappa_gui.exe.

---------------------------------------------------------
3. Updating the Conda Environment
---------------------------------------------------------

1. Make changes in your development environment.
2. Export it:

    conda pack -n babappa_env -o babappa_env.tar.gz

3. Replace the existing babappa_env.tar.gz in the build folder.

---------------------------------------------------------
4. Building the Installer
---------------------------------------------------------

1. Open "Inno Setup Compiler".
2. Load babappa_installer.iss.
3. Build → produces babappa_installer_2.0.exe.

---------------------------------------------------------
5. Uninstall Behavior
---------------------------------------------------------

- Runs UninstallRun → kills uvicorn, deletes env and project inside WSL.
- Removes files from C:\Program Files\babappa.

---------------------------------------------------------
6. Debugging
---------------------------------------------------------

- API logs: ~/babappa_uvicorn.log inside WSL.
- Installer logs: install.log in the build folder.
- If GUI shows "Internal Server Error", check babappa_uvicorn.log.

---------------------------------------------------------
7. Common Pitfalls
---------------------------------------------------------

- Ensure babappa_api.py is included in babappa_project during install.
- Make sure start_babappa.sh points one level up (ROOT_DIR) for tarball & installer.
- Fix permissions (chmod -R) so logs can be written.

---------------------------------------------------------
8. Release Checklist
---------------------------------------------------------

[ ] Update GUI → rebuild with PyInstaller.
[ ] Export new conda env → update babappa_env.tar.gz.
[ ] Update .iss version number.
[ ] Rebuild installer in Inno Setup.
[ ] Test install + uninstall on a clean machine.
