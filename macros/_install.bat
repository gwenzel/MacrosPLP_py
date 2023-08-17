call %USERPROFILE%\Anaconda3\Scripts\activate
call conda create -n plp python=3.9
call conda activate plp
cd %USERPROFILE%\MacrosPLP_py
call python setup.py develop
@pause