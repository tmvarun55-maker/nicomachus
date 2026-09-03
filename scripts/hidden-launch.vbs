' Launch the Nicomachus server supervisor with no visible window.
' WindowStyle 0 = hidden; there is no console flash, nothing in the taskbar.
Set sh = CreateObject("WScript.Shell")
root = sh.CurrentDirectory
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
wrapper = fso.BuildPath(scriptDir, "serve-forever.ps1")
sh.CurrentDirectory = fso.GetParentFolderName(scriptDir)
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & wrapper & """", 0, False
