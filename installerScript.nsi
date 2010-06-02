;NSIS Modern User Interface
;Start Menu Folder Selection Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "Ilastik"
  OutFile "ilastik_setup.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\Ilastik"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\Ilastik" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

;--------------------------------
;Variables

  Var StartMenuFolder

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Ilastik" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
  
  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
  
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Ilastik" SecDummy

  SectionIn RO
  SetOutPath "$INSTDIR"
  
  FILE /r *
  
  ;Store installation folder
  WriteRegStr HKCU "Software\Ilastik" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"

    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Ilastik.lnk" "$INSTDIR\ilastikMain.exe"  
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

Section "Demo Files" SecDemo

  SetOutPath "$INSTDIR"
  
  FILE ..\..\..\..\gui\demo\a_wood.jpg
  FILE ..\..\..\..\gui\demo\b_animal1.jpg
  FILE ..\..\..\..\gui\demo\c_cells_1.png
  FILE ..\..\..\..\gui\demo\c_cells_2.png
  FILE ..\..\..\..\gui\demo\c_cells_3.png
  FILE ..\..\..\..\gui\demo\d_gewebe_1.png
  FILE ..\..\..\..\gui\demo\e_letter.png
  FILE ..\..\..\..\gui\demo\f_animal1_gray.jpg
  FILE ..\..\..\..\gui\demo\3d_example_1.h5
  FILE ..\..\..\..\gui\demo\3d_example_2.h5
  FILE ..\..\..\..\gui\demo\ms_example_1.h5
  FILE ..\..\..\..\gui\demo\2d_cells_apoptotic.png
  FILE ..\..\..\..\gui\demo\2d_cells_apoptotic_small.png
  FILE ..\..\..\..\gui\demo\2d_cells_firstType.png
  FILE ..\..\..\..\gui\demo\2d_cells_mixed.png
  FILE ..\..\..\..\gui\demo\2d_cells_secondType.png
  FILE ..\..\..\..\gui\demo\2d_cells_twoTypes.png
  FILE ..\..\..\..\gui\demo\2d_texture.png
  FILE ..\..\..\..\gui\demo\CoventryCathedral.png
  FILE ..\..\..\..\gui\demo\calyx.h5
  FILE ..\..\..\..\gui\demo\neuro1.h5
  

  
SectionEnd



;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecDummy ${LANG_ENGLISH} "Ilastik binaries (required)"

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDemo} "Demo Files"
  !insertmacro MUI_FUNCTION_DESCRIPTION_END
 
;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...

  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$INSTDIR"
  
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    
  Delete "$SMPROGRAMS\ilastikMain.exe"
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
  RMDir /r "$SMPROGRAMS\$StartMenuFolder"
  
  DeleteRegKey /ifempty HKCU "Software\Ilastik"

SectionEnd