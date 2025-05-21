!include "MUI2.nsh"

; General
Name "YTMTools"
OutFile "YTMTools-Setup.exe"
InstallDir "$PROGRAMFILES\YouTubeMusicTools"
RequestExecutionLevel admin

; Icons
Icon "../assets\icons\img.ico"
UninstallIcon "../assets\icons\img.ico"

!define BUNDLE_DIR "../ytmtools.dist/main.dist"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\ytmtools.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Run YTMTools now"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Install YTMTools" SecInstall
  SetOutPath "$INSTDIR"
  File /r "${BUNDLE_DIR}\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Registry entries for Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools" \
                   "DisplayName" "YouTube Music Tools"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools" \
                   "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools" \
                   "DisplayIcon" "$INSTDIR\assets\icons\img.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools" \
                   "Publisher" "YTMTools"

  ; Permissions
  ExecWait 'cmd.exe /c icacls "$INSTDIR" /grant Users:(OI)(CI)F'
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
  CreateDirectory "$SMPROGRAMS\YouTubeMusicTools"
  CreateShortCut "$SMPROGRAMS\YouTubeMusicTools\YTMTools.lnk" \
                 "$INSTDIR\ytmtools.exe" \
                 "" \
                 "$INSTDIR\assets\icons\img.ico"
  CreateShortCut "$SMPROGRAMS\YouTubeMusicTools\Uninstall.lnk" \
                 "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Desktop Shortcut" SecDesktop
  CreateShortCut "$DESKTOP\YTMTools.lnk" \
                 "$INSTDIR\ytmtools.exe" \
                 "" \
                 "$INSTDIR\assets\icons\img.ico"
SectionEnd

; Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecInstall} "Install YTMTools application files."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create shortcuts in the Start Menu."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create a shortcut on the Desktop."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section
Section "Uninstall" SecUninstall
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\YouTubeMusicTools\YTMTools.lnk"
  Delete "$SMPROGRAMS\YouTubeMusicTools\Uninstall.lnk"
  RMDir "$SMPROGRAMS\YouTubeMusicTools"
  Delete "$DESKTOP\YTMTools.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\YTMTools"
SectionEnd
