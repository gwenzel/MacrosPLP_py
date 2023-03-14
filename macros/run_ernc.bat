call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp
: Change directory to code location
cd %USERPROFILE%\MacrosPLP_py
: Run ernc script
call python macros/ernc.py
: Sleep 5 seconds to show results or errors
timeout 5

: On server:
: set file=%1
: call %USERPROFILE%\Anaconda3\Scripts\activate
: call conda activate plp
: :cd D:\PLP_macros_python
: :call python macros/ernc.py
: call ernc -f %file%
: : Sleep 5 seconds to show results or errors
: timeout 5