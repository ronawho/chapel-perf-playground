#!/usr/bin/env python3
# encoding: utf-8

"""
shootoutreport.py

This script does the following:
1. Pulls latest data from benchmarksgame repository,
   unless 'data' specified in config file
2. Generates shootout graphs from data
3. Converts the pngs into summary pdfs in plots/
"""

#
# TODO
# - Add clean option to wipe data / plots directory?
#

import argparse
import os
import subprocess
import shlex
import sys

import shootouts
import shootouts_overview

try:
    import yaml
except ImportError:
    print('Required modules not installed')
    print('Try `pip3 install -r requirements.txt`')
    raise ImportError


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', '-c', help='yaml configuration file', default='default.yaml')

    args = parser.parse_args()
    return args


def check_command(command):
    """Check if command exists using 'which cmd'"""
    cmd = 'which {0}'.format(command)
    output = ''

    try:
        subprocess.check_output(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        output = '{0}: not found\n'.format(command)
    return output


def commands_installed():
    """Check if commands are installed"""
    print('Checking if all necessary commands available')
    errorstring =  ''
    errorstring += check_command('cvs')
    errorstring += check_command('convert')
    if len(errorstring) > 0:
        print('Some prerequisite commands were not found:')
        print(errorstring)
        print('Please install the prerequisites and try again')
        return False
    print('All necessary commands are available')
    return True


def pull_benchmarks_data():
    """Pull latest data"""
    CLBG_repo = ':pserver:anonymous@cvs.debian.org:/cvs/benchmarksgame'
    CLBG_dir = 'benchmarksgame/website/websites/u64q/data'
    cmd = 'cvs -d {0} checkout {1}'.format(CLBG_repo, CLBG_dir)
    try:
        subprocess.check_output(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        print('Error occurred during cvs checkout')
        print(err.stderr.decode('utf-8'))
        raise err


def make_plots(configs):
    shootouts.language_all(configs, save='plots/languages')
    shootouts.language_overview(configs, save='plots/overview')
    shootouts.shootout_all(configs, save='plots/shootouts')
    shootouts_overview.language_lines(configs, save='plots/overview_lines')

def convert_plots():

    try:
        cmd = 'convert plots/overview/*.png  plots/overview.pdf'
        subprocess.check_output(shlex.split(cmd))
        cmd = 'convert plots/languages/*.png plots/languages.pdf'
        subprocess.check_output(shlex.split(cmd))
        cmd = 'convert plots/shootouts/*.png plots/shootouts.pdf'
        subprocess.check_output(shlex.split(cmd))
        cmd = 'convert plots/overview_lines/*.png plots/overview_lines.pdf'
        subprocess.check_output(shlex.split(cmd))
    except subprocess.CalledProcessError as err:
        print('Error occurred during plot conversion')
        print(err.stderr.decode('utf-8'))
        raise err


def main(configfile):
    """Generate shootout reports"""
    if not os.path.exists(configfile):
        print(configfile, ' does not exist!')
        sys.exit(1)

    print('Using {0} as configuration file'.format(configfile))

    configs = yaml.load(open(configfile, 'r'))

    # Check commands
    if not commands_installed():
        sys.exit(1)

    # Check for data field, pull data if needed
    if 'data' not in configs.keys():
        configs['data'] = 'benchmarksgame/website/websites/u64q/data/data.csv'
        print('No data field in {0} --'.format(configfile))
        print('Pulling latest data from benchmarksgame repository')
        pull_benchmarks_data()

    # Plot data
    make_plots(configs)

    # Convert plots
    convert_plots()


if __name__ == '__main__':
    ARGS = parse_args()

    main(ARGS.config)
