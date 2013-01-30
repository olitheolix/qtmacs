set WshShell = WScript.CreateObject("WScript.Shell" )
set oShellLink = WshShell.CreateShortcut(Wscript.Arguments.Named("dest") & ".lnk")
oShellLink.TargetPath = Wscript.Arguments.Named("src")
oShellLink.Description = Wscript.Arguments.Named("desc")
oShellLink.IconLocation = Wscript.Arguments.Named("icon")
oShellLink.WindowStyle = 1
oShellLink.Save
