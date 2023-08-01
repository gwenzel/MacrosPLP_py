from setuptools import setup, find_packages

requirements = [
    'pandas',
    'numpy',
    'pyxlsb',
    'openpyxl'
]

setup(
    name='macros_plp',
    version='0.0.2',
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
            "main = macros.main:main",
            "filt = macros.filter_files:main",
            "postpro = postpro.main:main",
            "ernc = macros.ernc:main",
            "dda = macros.demanda:main",
            "bar = macros.barras:main",
            "mantcen = macros.mantcen:main",
            "cvar = macros.cvariable:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)