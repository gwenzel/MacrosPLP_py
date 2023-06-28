# MacrosPLP_py

PLP Macros refactored using python and pandas for better performance.

The code is callable from different entry points, associated to each button of the old Macros.

## How to install (developer)

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

To generate the wheel file for user install (which is an image of the current state of the project), the commands are the following:

```
call conda activate plp
cd PROJECT_DIRECTORY
call python setup.py sdist bdist_wheel
```

The wheel file should be generated in the project directory, in the dist folder.

## How to install (user)

From command line, run the following commands to create the virtual environment called plp

```
call %USERPROFILE%\Anaconda3\Scripts\activate
call conda create -n plp Python=3.9
```

Then, activate the environment, and install the wheel file generated

```
call conda activate plp
call pip install [wheel_file_path]
```

Example name of wheel_file_path: "D:\Python_wheels\macros_plp-0.0.2-py3-none-any.whl"

To avoid having conflicting packages on the same environment, new wheel files are being installed in new environments, labeled in the same way. For example, version 0.0.2 was installed in the environment "plp_v02".

## How to use

The idea is to be able to call each script and have it create the required files on the Temp folder.

Please note that these scripts will ask for the path of the IPLP input file, which must already have created a Temp folder with the files on the Dat subfolder.

Before running these scripts, make sure you have activated the previously created virtual environment.

```
call %USERPROFILE%\Anaconda3\Scripts\activate
call conda activate plp
```

### ERNC

Entry point _ernc_ calls the script in _macros/ernc.py_.

If there is no -f (file) argument, the program will ask for the location.

```
call python ernc -f IPLP_FILENAME
```

### Demanda

Entry point _dda_ calls the script in _macros/demanda.py_.

If there is no -f (file) argument, the program will ask for the location.

```
call python dda -f IPLP_FILENAME
```