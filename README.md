# MacrosPLP_py

PLP Macros refactored using python and pandas for better performance.

The code is callable from different entry points, associated to each button of the old Macros.

## How to install (developer)

From command line, run the following commands to create the virtual environment called plp.

Note that you can omit the call statement when writing directly on cmd, but not when you are calling the commands from a batch (.bat) file.

```
%USERPROFILE%\Anaconda3\Scripts\activate
conda create -n plp Python=3.9
```

Then, activate the environment, go to the project directory and install using the setup.py file. Mode, "develop" is chosen so that future changes can be easily integrated

```
conda activate plp
cd <PROJECT_DIRECTORY>
pip install -e .
```

To generate the wheel file for user install (which is an image of the current state of the project), the commands are the following:

```
conda activate plp
cd <PROJECT_DIRECTORY>
python setup.py sdist bdist_wheel
```

The wheel file should be generated in the project directory, in the dist folder.

## How to install (user)

From command line, run the following commands to create the virtual environment called plp

```
%USERPROFILE%\Anaconda3\Scripts\activate
conda create -n plp Python=3.9
```

Then, activate the environment, and install the wheel file generated

```
conda activate plp
pip install <wheel_file_path>
```

Example name of wheel_file_path: "D:\Python_wheels\macros_plp-0.0.2-py3-none-any.whl"

To avoid having conflicting packages on the same environment, new wheel files are being installed in new environments, labeled in the same way. For example, version 0.0.2 was installed in the environment "plp_v02".

## How to use

You will be able to call each script separately and have it create the required files on the Temp folder.

Please note that these scripts will ask for the path of the IPLP input file, which must already have created a Temp folder with the files on the Dat subfolder.

Before running these scripts, make sure you have activated the previously created virtual environment.

```
%USERPROFILE%\Anaconda3\Scripts\activate
conda activate plp
```

Note for most commands: if there is no -f (file) argument, the program will ask for the location.


### Blocks

The following command creates: plpeta.dat and Etapa2Dates.csv.
```
blo -f IPLP_FILENAME
```

### Buses

The following command creates: plpbar.dat, uni_plpbar.dat and plpbar_full.dat.
```
bar -f IPLP_FILENAME
```

### Generators

The following commanda creates: plpcnfce.dat and plptec.dat.
```
cen -f IPLP_FILENAME
```

### Generator Maintenance

The following commanda creates: plpmance_ini.dat
```
mantcen -f IPLP_FILENAME
```

### Renewable energy profiles

The following command creates the renewable profiles. It needs the plpmance_ini.dat file, to then append the data to create plpmance.dat.
```
ernc -f IPLP_FILENAME
```

### Demand

The following command creates: plpdem.dat, uni_plpdem.dat and plpfal.prn.
```
dda -f IPLP_FILENAME
```

### Variable Cost

The following command creates: plpcosce.dat.
```
cvar -f IPLP_FILENAME
```

### Lines

The following command creates: plpcnfli.dat.
```
lin -f IPLP_FILENAME
```

### Lines maintenance

The following commands create: plpmanli.dat and plpmanlix.dat, respectively.
```
manli -f IPLP_FILENAME
manlix -f IPLP_FILENAME
```

### Inflows

The following command creates the PLP inflow file: plpaflce.dat.
```
afl -f IPLP_FILENAME --plp
```

The same script is used to create the Plexos inflow files, Storage_NaturalInflow.csv
```
afl -f IPLP_FILENAME --plx
```

Both commands can be used at once as well, activating both flags
```
afl -f IPLP_FILENAME --plp --plx
```

### Plexos PIB files

The following command is used to create all Plexos PIB files in the CSV folder:
```
plx -f IPLP_FILENAME
```

Please note that this command requires the creation of certain files in the _Temp/df_ folder. This is done to avoid processing the same information more than once.

## How to check errors

Logs are created in the folder _Temp/log_. You can check if any of the different routines had an error there.