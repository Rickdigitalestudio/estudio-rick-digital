' ESTUDIO RICK DIGITAL - abre como programa sem janela preta
Set ws = CreateObject("WScript.Shell")
appDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
page = "file:///" & Replace(appDir & "\index.html", "\", "/")
chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
edge1 = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
edge2 = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
Set fso = CreateObject("Scripting.FileSystemObject")
profile = appDir & "\.app-profile"
If fso.FileExists(chrome) Then
  ws.Run """" & chrome & """ --app=""" & page & """ --user-data-dir=""" & profile & """", 1, False
ElseIf fso.FileExists(edge1) Then
  ws.Run """" & edge1 & """ --app=""" & page & """ --user-data-dir=""" & profile & """", 1, False
ElseIf fso.FileExists(edge2) Then
  ws.Run """" & edge2 & """ --app=""" & page & """ --user-data-dir=""" & profile & """", 1, False
Else
  ws.Run """" & appDir & "\index.html""", 1, False
End If
