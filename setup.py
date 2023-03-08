from setuptools import setup, find_packages

requirements = [
    'pandas',
    'numpy'
]

setup(
    name='macros_plp',
    version='0.0.1',
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
            "ernc: = macros.ernc:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)