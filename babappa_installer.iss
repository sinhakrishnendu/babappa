; Babappa Installer - full script
; Drop this .iss into the same folder as:
;   - dist\babappa_gui.exe
;   - babappa_clean.tar.xz
;   - ubuntu-22.04-wsl-rootfs.tar.gz   (optional; included if present)
; and compile with Inno Setup 6+

[Setup]
; Basic app info
AppName=Babappa GUI
AppVersion=1.0
AppPublisher=Krishnendu Sinha, Jhargram Raj College
DefaultDirName={autopf}\Babappa
DefaultGroupName=Babappa
OutputBaseFilename=Babappa_Installer
OutputDir=Output
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Require admin to write to Program Files and run wsl install/import
PrivilegesRequired=admin

[Files]
; GUI exe
Source: "dist\babappa_gui.exe"; DestDir: "{app}"; Flags: ignoreversion

; The main WSL tar.xz you will import
Source: "babappa_clean.tar.xz"; DestDir: "{app}"; Flags: ignoreversion

; Optional additional rootfs (include only if present at build time)
Source: "ubuntu-22.04-wsl-rootfs.tar.gz"; DestDir: "{app}"; Flags: ignoreversion

; Small extras (icons, readme)
Source: "butterfly_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Babappa GUI"; Filename: "{app}\babappa_gui.exe"
Name: "{commondesktop}\Babappa GUI"; Filename: "{app}\babappa_gui.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

; We handle WSL commands from the [Code] section to avoid quoting issues and to allow checks

[Code]
procedure MsgInfo(const S: String);
begin
  MsgBox(S, mbInformation, MB_OK);
end;

function IsWSLInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to run 'wsl --version' and check exit code
  if Exec('wsl.exe', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode = 0)
  else
    Result := False;
end;

procedure RunWSLUnregister();
var
  ResultCode: Integer;
begin
  // Unregister any existing 'Babappa' distro. Ignore failures.
  Exec('wsl.exe', '--unregister Babappa', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure RunWSLImport();
var
  ResultCode: Integer;
  AppPath, WslDir, TarPath, Params: String;
begin
  AppPath := ExpandConstant('{app}');
  WslDir := AppPath + '\wsl';
  TarPath := AppPath + '\babappa_clean.tar.xz';

  if not FileExists(TarPath) then
  begin
    MsgBox('WSL tarball not found:' + #13#10 + TarPath + #13#10 +
           'Import skipped. Make sure the tarball is present next to the installer or included in the build.',
           mbError, MB_OK);
    Exit;
  end;

  // Ensure the directory exists (WSL import will create the distro, but create folder to be safe)
  if not DirExists(WslDir) then
  begin
    if not ForceDirectories(WslDir) then
    begin
      MsgBox('Failed to create directory: ' + WslDir + #13#10 +
             'Ensure you have sufficient privileges.', mbError, MB_OK);
      Exit;
    end;
  end;

  // Build parameters with quoted paths (handles spaces)
  Params := '--import Babappa "' + WslDir + '" "' + TarPath + '" --version 2';

  if not Exec('wsl.exe', Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('Failed to invoke wsl.exe for import. Please run the following command manually (elevated):' + #13#10#13#10 +
           'wsl --import Babappa "' + WslDir + '" "' + TarPath + '" --version 2',
           mbError, MB_OK);
  end
  else if ResultCode <> 0 then
  begin
    MsgBox('wsl import returned exit code ' + IntToStr(ResultCode) +
           '. You may need to run the import manually or check WSL logs.', mbInformation, MB_OK);
  end
  else
  begin
    MsgInfo('WSL distribution "Babappa" imported successfully.');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  MsgText: String;
begin
  // Use ssPostInstall so that files (including the tarball) are already copied to {app}
  if CurStep = ssPostInstall then
  begin
    // If WSL is missing, offer to run 'wsl --install' (this will require reboot)
    if not IsWSLInstalled() then
    begin
      MsgText := 'WSL2 does not appear to be installed on this system.' + #13#10#13#10 +
                 'The installer will now attempt to run "wsl --install".' + #13#10#13#10 +
                 'If installation proceeds, you may be prompted to restart your computer.' + #13#10#13#10 +
                 'After reboot, please rerun the Babappa installer to import the Babappa WSL distro.';
      if MsgBox(MsgText, mbInformation, MB_OKCANCEL) = IDOK then
      begin
        // Run via PowerShell to ensure proper environment
        ShellExec('', 'powershell.exe', '-Command "wsl --install"', '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode);
        // Stop further automated steps — user should rerun installer after reboot/installation
        Exit;
      end
      else
      begin
        // User cancelled; skip import
        Exit;
      end;
    end;

    // WSL exists: perform unregister + import (unregister may fail if distro doesn't exist; that's OK)
    RunWSLUnregister();
    RunWSLImport();
  end;
end;
