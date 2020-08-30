@echo off

echo.Loading Qt environment...
REM (pushd because qtenv2.bat changes dir)
pushd .
call "%QTDIR%"\bin\qtenv2.bat
popd
echo.... Done.

echo.Loading VS environment...
call "%VS110COMNTOOLS%VsDevCmd.bat"
echo.... Done.

echo.Cleaning up previous dependencies...
pushd "dependencies"
if exist "qt" (
rd /s /q qt
)
popd

echo.Gathering MeveaSolver.exe dependencies...
windeployqt --dir dependencies\qt --libdir dependencies\qt dependencies\sentinel\MeveaSolver.exe --no-translations --verbose 0 --release

echo.... Done.

pause
