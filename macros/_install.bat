call %USERPROFILE%\Anaconda3\Scripts\activate
call conda create -n plp python=3.9
call conda activate plp
cd D:\PLP_macros_python
call python setup.py develop
@pause