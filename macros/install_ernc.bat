call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp
cd D:\PLP_macros_python
call python setup.py develop
@pause
:call python ernc
:call python macros/ernc.py