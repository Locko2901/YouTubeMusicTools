[Setup]
AppName=YTMTools
AppVersion=2.1.3
DefaultDirName={autopf}\YouTubeMusicTools
DefaultGroupName=YouTubeMusicTools
OutputDir=..\ytmtools.dist
OutputBaseFilename=YTMTools-Setup
SetupIconFile=..\assets\icons\img.ico
UninstallDisplayIcon={app}\assets\icons\img.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
DisableDirPage=no

[Files]
Source: "..\ytmtools.dist\main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "..\assets\icons\img.ico"; DestDir: "{app}\assets\icons"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Create shortcuts:"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Create shortcuts:";
Name: "cleaninstall"; Description: "Clean installation (removes all previous user data)"; GroupDescription: "Installation options:"; Flags: unchecked; Check: not IsFirstInstall

[Icons]
Name: "{group}\YTMTools"; Filename: "{app}\ytmtools.exe"; IconFilename: "{app}\assets\icons\img.ico"; Tasks: startmenuicon
Name: "{group}\Uninstall YTMTools"; Filename: "{uninstallexe}"; Tasks: startmenuicon
Name: "{commondesktop}\YTMTools"; Filename: "{app}\ytmtools.exe"; IconFilename: "{app}\assets\icons\img.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\ytmtools.exe"; Description: "Run YTMTools now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\YTMTools"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Code]
function IsAppRunning(): Boolean;
var
  StdOutFile: String;
  S: AnsiString;
  Dummy: Integer;
begin
  Result := False;
  StdOutFile := ExpandConstant('{tmp}\ytmtools_tasklist.txt');
  if Exec('cmd.exe', '/C tasklist /FI "IMAGENAME eq ytmtools.exe" > "' + StdOutFile + '"', '', SW_HIDE, ewWaitUntilTerminated, Dummy) then
  begin
    if LoadStringFromFile(StdOutFile, S) then
    begin
      if Pos('ytmtools.exe', S) > 0 then
        Result := True;
    end;
    DeleteFile(StdOutFile);
  end;
end;

function IsAlreadyInstalled(): Boolean;
var
  UninstallString: String;
begin
  Result := RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools_is1', 'UninstallString', UninstallString);
  if not Result then
    Result := RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools_is1', 'UninstallString', UninstallString);
end;

function IsFirstInstall(): Boolean;
var
  UserDataDir: String;
begin
  Result := not IsAlreadyInstalled();
  
  if Result then
  begin
    UserDataDir := ExpandConstant('{localappdata}\YouTubeMusicTools');
    if DirExists(UserDataDir) then
      Result := False;
  end;
end;

procedure CleanUserData();
var
  UserDataDir: String;
begin
  UserDataDir := ExpandConstant('{localappdata}\YouTubeMusicTools');
  if DirExists(UserDataDir) then
  begin
    DelTree(UserDataDir, True, True, True);
  end;
end;

function InitializeSetup(): Boolean;
begin
  if IsAlreadyInstalled() then
  begin
    if MsgBox('YTMTools is already installed. Do you want to reinstall it?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      exit;
    end;
  end;
  
  if IsAppRunning() then
  begin
    MsgBox('YTMTools is currently running. Please close it before installing.', mbError, MB_OK);
    Result := False;
    exit;
  end;
  
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    // Only clean user data if it's not a first install and clean install is selected
    if WizardIsTaskSelected('cleaninstall') and not IsFirstInstall() then
    begin
      CleanUserData();
    end;
  end;

  if CurStep = ssPostInstall then
  begin
    // Create an empty marker file to indicate installed version
    SaveStringToFile(ExpandConstant('{app}\.installed'), '', False);
  end;
end;

function InitializeUninstall(): Boolean;
begin
  if IsAppRunning() then
  begin
    MsgBox('YTMTools is currently running. Please close it before uninstalling.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  LogDir: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Ask user if they want to remove user data during uninstallation
    if MsgBox('Do you want to remove all user data?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      LogDir := ExpandConstant('{localappdata}\YouTubeMusicTools');
      if DirExists(LogDir) then
        DelTree(LogDir, True, True, True);
    end;
  end;
end;
