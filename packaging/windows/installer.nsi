; NSIS installer for CouchTomato.
;
; Expects to be built from the PyInstaller onedir output (packaging/couchtomato.spec).
; Invoke with, e.g.:
;   makensis /DAPP_VERSION=4.1.0 /DDIST_DIR=C:\path\to\dist\CouchTomato /DICON_PATH=C:\path\to\favicon.ico installer.nsi

!define APP_NAME "CouchTomato"
!define COMPANY_NAME "CouchTomatoes"
!define EXE_NAME "CouchTomato.exe"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

!ifndef APP_VERSION
  !define APP_VERSION "0.0.0"
!endif
!ifndef DIST_DIR
  !error "DIST_DIR must be defined - path to the PyInstaller onedir output (dist/CouchTomato)"
!endif
!ifndef ICON_PATH
  !error "ICON_PATH must be defined - path to favicon.ico"
!endif

Name "${APP_NAME}"
OutFile "CouchTomato-Setup-${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "${UNINST_KEY}" "InstallLocation"
RequestExecutionLevel admin
Icon "${ICON_PATH}"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "${DIST_DIR}\*.*"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "${COMPANY_NAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\${APP_NAME}"
  DeleteRegKey HKLM "${UNINST_KEY}"
SectionEnd
