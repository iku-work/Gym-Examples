@echo off

REM set DEP_ROOT=
set MVS_PARSE=parse_mvs_deps2.py

if exist "CleanCopy_Excavator" (
rd /s /q CleanCopy_Excavator
)




pushd ..\Model

REM try to run all models from the same MPK
..\Installer\dependencies\mvs_parse\%MVS_PARSE% "Excavator.mvs" ..\Installer\CleanCopy_Excavator



popd


