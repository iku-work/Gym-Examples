@echo off
cls
echo This script will fetch the dependencies from network drive and svn.
echo You need to give your mevprojects username and password to do this.
echo NOTE: Before entering password, make sure no one is looking. It will be visible!
set /P svn_username="Enter your SVN username: "
set /P svn_password="..and your SVN password: "
cls
echo Thank you, ready to proceed.
pause

goto DependencyCopy

REM ==== Usage ====
:Usage
echo ===
echo Please make sure you have the proper X:\ drive mounted.
echo ===
pause
goto :EOF

REM ==== SVN error  ====
:SVNError
echo !!!!!!!!!!!!!!!!!!!!
echo There was an error in SVN operation. Try to run the whole script again.
echo !!!!!!!!!!!!!!!!!!!!
pause
goto :EOF

REM ==== Dependency svn modified error ====
:SVNUpdateError
echo !!!!!!!!!!!!!!!!!!!!
echo Error updating the SVN dependencies.
echo Make sure you have not modified anything under dependencies dir.
echo Then try to run the script again.
echo !!!!!!!!!!!!!!!!!!!!
pause
goto :EOF

REM --------------
:DependencyCopy

pushd dependencies
REM resources misc
if not exist "svn_misc" (
echo svn_misc does not exist, checking out...
svn checkout http://mevprojects/svn/mevea-resources/misc svn_misc --username %svn_username% --password %svn_password%
if %ERRORLEVEL% neq 0 goto SVNError
) else (
echo cleaning up and updating svn_misc ...
subwcrev.exe svn_misc -nm
if %ERRORLEVEL% neq 0 goto SVNUpdateError
svn cleanup svn_misc
if %ERRORLEVEL% neq 0 goto SVNError
svn update svn_misc --username %svn_username% --password %svn_password%
if %ERRORLEVEL% neq 0 goto SVNError
)

if exist "misc" (
rd /s /q misc
)
echo exporting svn_misc to misc ...
svn export svn_misc misc
if %ERRORLEVEL% neq 0 goto SVNError
REM -- End resources misc

if not exist "svn_resources" (
echo svn_resources does not exist, checking out...
svn checkout http://mevprojects/svn/mevea-resources/resources svn_resources --username %svn_username% --password %svn_password%
if %ERRORLEVEL% neq 0 goto SVNError
) else (
echo cleaning up and updating svn_resources ...
subwcrev.exe svn_resources -nm
if %ERRORLEVEL% neq 0 goto SVNUpdateError
svn cleanup svn_resources
if %ERRORLEVEL% neq 0 goto SVNError
svn update svn_resources --username %svn_username% --password %svn_password%
if %ERRORLEVEL% neq 0 goto SVNError
)

if exist "resources" (
rd /s /q resources
)
echo exporting svn_resources to resources ...
svn export svn_resources resources
if %ERRORLEVEL% neq 0 goto SVNError
REM --- End resources


if exist "mvs_parse" (
rd /s /q mvs_parse
)

if exist "mvs_parse" (
rd /s /q mvs_parse
)
echo fetching the mvs parsing script
mkdir mvs_parse
svn export http://mevprojects/svn/mevea-rnd/python_mvs_parse/parse_mvs_deps2.py mvs_parse\
if %ERRORLEVEL% neq 0 goto SVNError


popd

