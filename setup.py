from setuptools import setup, find_packages

requirements = [
    'pandas',
    'numpy',
    'pyxlsb',
    'openpyxl',
    'enlighten',
    'python-dateutil'
]

setup(
    name='macros_plp',
    version='2.2.0',
    description=('A package to replace PLP VBA macros'),
    author='George Wenzel',
    packages=find_packages(),
    install_requires=requirements,
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=['pytest'],
    extras_require={
        "notebooks": ['jupyter', 'ipyfilechooser'],
    },
    entry_points={
        "console_scripts": [
            "postpro = postpro.main:main",
            "filt = macros.filter_files:main",
            "bar = macros.bar:main",
            "dda = macros.dem:main",
            "mantcen = macros.mantcen:main",
            "ernc = macros.ernc:main",
            "cvar = macros.cvar:main",
            "lin = macros.lin:main",
            "manli = macros.manli:main",
            "manlix = macros.manlix:main",
            "afl = macros.inflows:main",
            "plx = macros.csv_plexos:main",
            "blo = macros.blo:main",
            "cen = macros.cen:main",
            "mat = macros.mat:main",
            "PLPIDSIMAPE_MANUAL = macros.PLPIDSIMAPE_MANUAL:main",
            "PLPMAULE_N = macros.PLPMAULE_N:main",
            "PLPLAJA_M = macros.PLPLAJA_M:main",
            "PLPCENPMAX = macros.PLPCENPMAX:main",
            "PLPCENRE = macros.PLPCENRE:main",
            "PLPDEB = macros.PLPDEB:main",
            "PLPEXTRAC = macros.PLPEXTRAC:main",
            "PLPFILTEMB = macros.PLPFILTEMB:main",
            "PLPRALCO = macros.PLPRALCO:main",
            "PLPVREBEMB = macros.PLPVREBEMB:main",
            "PLPPLEM1 =  macros.PLPPLEM1:main",
            "PLPPLEM2 =  macros.PLPPLEM2:main",
            "PLPMANEM_ETA = macros.PLPMANEM_ETA:main",
            "PLPMINEMBH = macros.PLPMINEMBH:main",
            "PLPGNL = macros.PLPGNL:main",
            "run_all = macros.run_all:main",
            "check_errors = utils.check_errors:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
