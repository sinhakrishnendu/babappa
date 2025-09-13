; babappa_installer.iss
; Inno Setup script for babappa installer (Option A: assets in top-level, GUI+script in dist)

#define AppName "babappa"
#define AppVersion "1.0"
#define AppPublisher "Krishnendu Sinha"
#define AppExeName "babappa_gui.exe"
#define AppDirName "{autopf}\babappa"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={#AppDirName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=babappa_installer_{#AppVersion}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\dist\{#AppExeName}
WizardStyle=modern
SetupIconFile="{#SourcePath}\butterfly_icon.ico"

[Files]
; GUI executable + startup script (in dist)
Source: "dist\babappa_gui.exe"; DestDir: "{app}\dist"; Flags: ignoreversion
Source: "dist\start_babappa.sh"; DestDir: "{app}\dist"; Flags: ignoreversion

; Conda environment archive + Miniconda installer (top-level)
Source: "babappa_env.tar.gz"; DestDir: "{app}"; Flags: ignoreversion
Source: "Miniconda3-latest-Linux-x86_64.sh"; DestDir: "{app}"; Flags: ignoreversion

; Project sources + API entrypoint into same project folder
Source: "babappa_project\*"; DestDir: "{app}\babappa_project"; Flags: recursesubdirs
Source: "babappa_api.py"; DestDir: "{app}\babappa_project"; Flags: ignoreversion

; Icons + docs
Source: "butterfly_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "butterfly_icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "README_INSTALLER.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Shortcut points directly to GUI
Name: "{group}\{#AppName}"; Filename: "{app}\dist\{#AppExeName}"; IconFilename: "{app}\butterfly_icon.ico"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\dist\{#AppExeName}"; IconFilename: "{app}\butterfly_icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[UninstallRun]
; Cleanup inside WSL on uninstall: stop API and remove env/project
Filename: "wsl.exe"; Parameters: "-d Ubuntu-22.04 -- bash -lc ""if [ -f ~/babappa_uvicorn.pid ]; then kill $(cat ~/babappa_uvicorn.pid) || true; fi; rm -rf ~/babappa_env ~/babappa_project ~/babappa_uvicorn.*"""; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;  // allow install to proceed
end;
