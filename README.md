# MacrosPLP_py

PLP Macros refactored using python and pandas for better performance.

The code is callable from different entry points, associated to each button of the old Macros.

## How to install

From command line, run the following commands to create the virtual environment called plp

```
call %USERPROFILE%\Anaconda3\Scripts\activate
call conda create -n plp Python=3.9
```

Then, activate the environment, go to the project directory and install using the setup.py file. Mode, "develop" is chosen so that future changes can be easily integrated

```
call conda activate plp
cd PROJECT_DIRECTORY
call python setup.py develop
```

## How to use

The idea is to be able to call each script and have it create the required files on the Temp folder.

Please note that these scripts will ask for the path of the IPLP input file, which must already have created a Temp folder with the files on the Dat subfolder.

### ERNC

Entry point "ernc" calls the script in macros/ernc.py.

If there is no -f (file) argument, the program will ask for the location.

```
call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp
cd PROJECT_DIRECTORY
call python ernc -f IPLP_FILENAME
```

### Demanda

Entry point "dda" calls the script in macros/demanda.py.

If there is no -f (file) argument, the program will ask for the location.

```
call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp
cd PROJECT_DIRECTORY
call python dda -f IPLP_FILENAME
```