@echo off
REM cls

set MEVEA_EXE_DIR="Z:\MeveaExe"
if not exist %MEVEA_EXE_DIR% ( goto :Usage )
if not exist %MEVEA_EXE_DIR%\Protected ( goto :Usage )

goto TargetCopy

REM ==== Usage ====
:Usage
echo ===
echo Please make sure you have the proper Z:\ drive mounted.
echo ===
pause
goto :EOF


REM --------------
:TargetCopy
pushd dependencies
REM -- sentinel protected stuff
if exist "sentinel" (
rd /s /q sentinel
)
mkdir sentinel
xcopy /y %MEVEA_EXE_DIR%\haspdinst.exe sentinel\
copy /y %MEVEA_EXE_DIR%\Protected\MeveaSolver.exe sentinel\MeveaSolver.exe
REM copy /y %MEVEA_EXE_DIR%\Protected\VisualChannel.exe sentinel\VisualChannel.exe
REM copy /y %MEVEA_EXE_DIR%\Protected\ExMeBusMIOClient.exe sentinel\ExMeBusMIOClient.exe
REM -- End sentinel stuff
REM


popd
pause

