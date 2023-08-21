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
    version='0.0.3',
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
            "filt = macros.0_filter_files:main",
            "bar = macros.1_bar:main",
            "dda = macros.3_dem:main",
            "mantcen = macros.5_mantcen:main",
            "ernc = macros.6_ernc:main",
            "cvar = macros.7_cvar:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
