@echo off
echo.First.. getting the dependencies..
pause
call get_dependencies.bat
call get_sentinel_protected_targets.bat
call get_qt_dependencies.bat


echo.
echo.
echo.Next.. making a clean copy of the model and adding related hardcoded stuff
call make_clean_copy.bat
call COPY_SOILPRESETS_DIR.bat
REM echo.If MPK not needed close the program
REM pause
REM call create_mpk_files.bat




pause
