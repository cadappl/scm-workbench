;
; -- workbench.iss --
;

[Code]
function InitializeSetup(): Boolean;
begin
    Result := true;
end;


[Setup]
AppName=WorkBench
AppVerName=WorkBench UNCONTROLLED
AppCopyright=Copyright (C) 2003-2012 Barry A. Scott
DefaultDirName={pf}\PySVN\WorkBench
DefaultGroupName=WorkBench for Subversion
UninstallDisplayIcon={app}\WorkBench.exe
DisableStartupPrompt=yes
InfoBeforeFile=info_before.txt
Compression=bzip/9

[Icons]
Name: "{group}\WorkBench"; Filename: "{app}\WorkBench.exe";
Name: "{group}\Documentation"; Filename: "{app}\workbench.html";
Name: "{group}\License"; Filename: "{app}\workbench_LICENSE.txt";
Name: "{group}\Web Site"; Filename: "http://pysvn.tigris.org";

[Files]

#include "..\msvc90_system_files.iss"

Source: "workbench_LICENSE.txt"; DestDir: "{app}";
Source: "..\..\..\Docs\WorkBench.html"; DestDir: "{app}";
Source: "WorkBench.exe"; DestDir: "{app}"; Flags: ignoreversion;
Source: "WorkBench.exe.manifest"; DestDir: "{app}"; Flags: ignoreversion;
