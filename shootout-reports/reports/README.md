# Shootouts reports

In this directory live the scripts needed to build the shootout plots:

- `shootoutreport.py`
    - master script / entry point
    - For more information, see `./shootoutreport.py --help`

- `shootouts.py`
    - Module containing all data manipulation and plotting functions

- `shootoutstesting.ipynb`
    - An interactive Jupyter notebook for testing & development

## Provided Configuration Files

- `default.yaml`
    - default config file

- `sample.yaml`
    - Sample config file with comments for demonstrative purposes

## Dependencies:

List of dependencies and how I installed them on OS X:

- python3
    - `brew install python3` on OS X
- requirements.txt (python modules)
    - `pip3 install -r requirements.txt`
    - Caveat: matplotlib can be finnicky with virtualenvs
- cvs
    - `brew install cvs` on OS X
- convert
    - `brew install ImageMagick` on OS X


## Data

While snapshots of the shootout data are stored in ../u64q, these scripts
will always pull the latest data from the CVS repository, unless a 'data' field
is specified in the config file (see the sample.yaml)

The intention is to store a snapshot of each release in ../u64q

The name 'u64q' is a mirror of the naming convention used in the benchmark repo

