call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp
: Change directory to code location
cd %USERPROFILE%\MacrosPLP_py
: Run ernc script
call python macros/ernc.py