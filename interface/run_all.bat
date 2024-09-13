@echo off
title Rutina Inputs PLP Python
@echo on
set version=%1
set file=%2
call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp_v_%version%
start dda -f %file%
start afl -f %file% --plp
start cvar -f %file%
call mantcen -f %file%
start ernc -f %file%
call bar -f %file%
call blo -f %file%
call cen -f %file%
call lin -f %file%
call manli -f %file%
call manlix -f %file%
: Other files
call mat -f %file%
: Sleep 10 seconds to show results or errors
timeout 20