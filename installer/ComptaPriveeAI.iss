; Programme uniquement. Aucune entrée ne cible les données LOCALAPPDATA.
#ifndef BundleDir
  #error BundleDir doit désigner le bundle onedir validé.
#endif
#ifndef InstallerOutput
  #error InstallerOutput doit désigner un dossier hors Git.
#endif
#ifndef ProductVersion
  #define ProductVersion "1.0.0"
#endif

[Setup]
; Stable pour les réinstallations et versions futures (dont 1.0.1).
AppId={{87DDB3EA-57D0-41CB-9B76-981F4C68E931}
AppName=ComptaPrivée AI
AppVersion={#ProductVersion}
; Nom du produit, pas une société légale déclarée.
AppPublisher=ComptaPrivée AI
DefaultDirName={autopf}\ComptaPriveeAI
DefaultGroupName=ComptaPrivée AI
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible and not arm64
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#InstallerOutput}
OutputBaseFilename=ComptaPriveeAI-Setup-{#ProductVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\ComptaPriveeAI.exe
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; Flags: unchecked

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ComptaPrivée AI"; Filename: "{app}\ComptaPriveeAI.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\ComptaPrivée AI"; Filename: "{app}\ComptaPriveeAI.exe"; WorkingDir: "{app}"; Tasks: desktopicon

; Pas de [Run] : le premier lancement doit utiliser le compte normal.
; Pas de [UninstallDelete] : aucune suppression de données utilisateur.
