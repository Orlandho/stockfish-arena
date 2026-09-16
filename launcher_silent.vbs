' Lanzador 100% silencioso para Windows (evita que aparezca la consola negra CMD)
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Obtener el directorio donde reside este script
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Ruta al interprete pythonw.exe (modo sin ventana) o python.exe
PythonwPath = ScriptDir & "\.venv\Scripts\pythonw.exe"
PythonPath = ScriptDir & "\.venv\Scripts\python.exe"
ScriptPath = ScriptDir & "\run_desktop.py"

If FSO.FileExists(PythonwPath) Then
    WshShell.CurrentDirectory = ScriptDir
    WshShell.Run """" & PythonwPath & """ """ & ScriptPath & """", 0, False
ElseIf FSO.FileExists(PythonPath) Then
    WshShell.CurrentDirectory = ScriptDir
    WshShell.Run """" & PythonPath & """ """ & ScriptPath & """", 0, False
Else
    MsgBox "No se encontro el entorno virtual .venv. Por favor ejecuta el instalador 'installer\instalar.bat' primero.", 16, "Stockfish 19 Arena"
End If
