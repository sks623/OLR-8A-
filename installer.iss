; OLR 8A - Inno Setup Script
; This creates a Windows installer that bundles the app + GhostScript

#define MyAppName "OLR 8A Automation"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sushant"
#define MyAppExeName "OLR8A.exe"

[Setup]
; App identity
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\OLR8A
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Output settings
OutputDir=Output
OutputBaseFilename=OLR8A_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
; Privileges
PrivilegesRequired=admin
; UI
WizardStyle=modern
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main application (built with PyInstaller)
Source: "dist\OLR8A.exe"; DestDir: "{app}"; Flags: ignoreversion

; GhostScript installer (download from https://ghostscript.com/releases/gsdnld.html)
; Place gs10060w64.exe in the same folder as this script
Source: "gs10060w64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: not IsGhostScriptInstalled

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install GhostScript silently if not already installed
Filename: "{tmp}\gs10060w64.exe"; Parameters: "/S"; StatusMsg: "Installing GhostScript..."; Flags: waituntilterminated; Check: not IsGhostScriptInstalled

; Launch app after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if GhostScript is already installed
function IsGhostScriptInstalled: Boolean;
var
  GSPath: String;
begin
  Result := False;

  // Check common installation paths
  if DirExists('C:\Program Files\gs') then
    Result := True
  else if DirExists('C:\Program Files (x86)\gs') then
    Result := True
  else if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\GPL Ghostscript') then
    Result := True
  else if RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\AFPL Ghostscript') then
    Result := True;

  if Result then
    Log('GhostScript already installed')
  else
    Log('GhostScript not found - will install');
end;

// Add GhostScript to PATH after installation
procedure CurStepChanged(CurStep: TSetupStep);
var
  GSBinPath: String;
  Path: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Find GhostScript bin folder (check newest versions first)
    if DirExists('C:\Program Files\gs\gs10.06.0\bin') then
      GSBinPath := 'C:\Program Files\gs\gs10.06.0\bin'
    else if DirExists('C:\Program Files\gs\gs10.03.1\bin') then
      GSBinPath := 'C:\Program Files\gs\gs10.03.1\bin'
    else if DirExists('C:\Program Files\gs\gs10.02.1\bin') then
      GSBinPath := 'C:\Program Files\gs\gs10.02.1\bin'
    else if DirExists('C:\Program Files (x86)\gs\gs10.06.0\bin') then
      GSBinPath := 'C:\Program Files (x86)\gs\gs10.06.0\bin'
    else if DirExists('C:\Program Files (x86)\gs\gs10.03.1\bin') then
      GSBinPath := 'C:\Program Files (x86)\gs\gs10.03.1\bin';

    if GSBinPath <> '' then
    begin
      // Get current PATH
      if RegQueryStringValue(HKEY_LOCAL_MACHINE,
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
        'Path', Path) then
      begin
        // Add GhostScript to PATH if not already there
        if Pos(LowerCase(GSBinPath), LowerCase(Path)) = 0 then
        begin
          Path := Path + ';' + GSBinPath;
          RegWriteStringValue(HKEY_LOCAL_MACHINE,
            'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
            'Path', Path);
          Log('Added GhostScript to PATH: ' + GSBinPath);
        end;
      end;
    end;
  end;
end;
