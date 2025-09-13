Babappa v2.0
============

Welcome! This is the Babappa application installer. 
Follow these instructions carefully to install and use Babappa.

---------------------------------------------------------
1. What You Need Before Installation
---------------------------------------------------------
- Windows 10 or 11 (64-bit).
- Windows Subsystem for Linux (WSL) with Ubuntu 22.04 installed.
  If WSL or Ubuntu 22.04 is missing, the installer will tell you. 
  In that case, open PowerShell as Administrator and run:

      wsl --install -d Ubuntu-22.04

  Then restart your computer before continuing.

---------------------------------------------------------
2. Installing Babappa
---------------------------------------------------------
1. Double-click the installer file (babappa_installer_2.0.exe).
2. Accept the license and follow the steps.
3. The application will be installed into:

      C:\Program Files\babappa

4. A shortcut named "Babappa" will appear on your Desktop and Start Menu.

---------------------------------------------------------
3. First Run
---------------------------------------------------------
1. Double-click the "Babappa" shortcut.
2. The program will prepare its environment inside WSL:
   - Installs Miniconda if not already installed.
   - Restores the Babappa environment from babappa_env.tar.gz.
   - Copies Babappa project files into WSL.
   - Starts the Babappa API server in the background.
3. Once the API is ready, the Babappa GUI window will appear.

---------------------------------------------------------
4. Using the GUI
---------------------------------------------------------
1. Select an input FASTA file using the "Browse" button.
2. Select an output folder where results should be saved.
3. Choose a model from the drop-down menu:
   - "clip"
   - "clipgard"
   - "normal"
4. Click "Run Analysis".
5. Logs will appear in the bottom window as the analysis runs.
6. When finished, check your chosen output folder for results.

---------------------------------------------------------
5. Troubleshooting
---------------------------------------------------------
- If the GUI shows "Internal Server Error":
  → Check the log file inside WSL:

      cat ~/babappa_uvicorn.log

- If Babappa says the API did not start:
  → Make sure WSL Ubuntu 22.04 is installed and working:

      wsl -l -v

- If the input or output folder cannot be selected:
  → Ensure you have permission to read/write in that folder.

- To completely reset Babappa:
  1. Uninstall Babappa from "Add or Remove Programs".
  2. Delete the folders:
        C:\Program Files\babappa
        ~/babappa_env
        ~/babappa_project
        ~/babappa_uvicorn.*

---------------------------------------------------------
6. Uninstalling Babappa
---------------------------------------------------------
1. Open "Add or Remove Programs" in Windows.
2. Find "Babappa" and click "Uninstall".
3. The uninstaller will stop the API, remove the environment, and delete all Babappa files.

---------------------------------------------------------
7. Support
---------------------------------------------------------
If you encounter issues that cannot be solved with the steps above, please contact:

    Developer: Krishnendu Sinha
    Email: dr.krishnendusinha@gmail.com

---------------------------------------------------------
Thank you for using Babappa!
---------------------------------------------------------
