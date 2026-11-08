; SoundKeys Windows Installer
; Keep this file in the project root, alongside SoundKeys.ico and the dist folder.

#define MyAppName "SoundKeys"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SoundKeys"
#define MyAppExeName "SoundKeys.exe"

[Setup]
AppId={{A7D9C1E4-6B2F-4A83-9D51-2F8C7B6E104A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SoundKeys
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=SoundKeys.ico
OutputDir=Output
OutputBaseFilename=SoundKeys_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startup"; Description: "Launch SoundKeys when Windows starts"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
Source: "dist\SoundKeys\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "SoundKeys.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\SoundKeys"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\SoundKeys.ico"
Name: "{autodesktop}\SoundKeys"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\SoundKeys.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SoundKeys"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SoundKeys"; ValueData: """{app}\SoundKeys.exe"" --startup"; Flags: uninsdeletevalue; Tasks: startup


[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'SoundKeys');
end;
