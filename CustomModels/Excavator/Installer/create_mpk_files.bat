@echo off

setlocal 
REM Check for installed Mevea Simulation Software
for /F "usebackq skip=2 tokens=2,*" %%A in (`reg query "HKLM\SOFTWARE\Wow6432Node\Mevea\Mevea Simulation Software" /v "InstallPath" 2^>nul`) do set "MEVSIMPATH=%%B"

if defined MEVSIMPATH (
	set SOLVER_EXE="%MEVSIMPATH%\bin\MeveaSolver.exe"
) else (
	echo !!! No installed Mevea Simulation Software, trying default path for solver... !!!
	set SOLVER_EXE="C:\Program Files (x86)\Mevea\bin\MeveaSolver.exe"
)

REM create the dir we will be generating the MPK file
if exist MPK (
rd /s /q MPK
)
mkdir MPK

pushd CleanCopy_Excavator

echo Packing the Excavator model files ...
%SOLVER_EXE% -mpk "Model\Excavator.mvs"

popd


echo All done.

endlocal
rem pause
