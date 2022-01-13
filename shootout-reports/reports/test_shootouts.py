#!/usr/bin/env python3
# encoding: utf-8


# Standard library imports
import unittest

# External imports
try:
    from scipy.stats.mstats import gmean
    import pandas as pd
    import yaml
except ImportError:
    print('Required modules not installed')
    print('Try `pip3 install -r requirements.txt`')
    raise ImportError

# Local imports
import shootouts

class ShootoutsTests(unittest.TestCase):
    """Tests for shootouts.py"""

    def test_mean(self):
        pass

    def test_stddev(self):
        pass

    def test_gmean(self):
        #x=gmean(group.codesize.values.tolist())
        #y=gmean(group.time.values.tolist()
        pass

    def test_gstddev(self):
        configfile = 'test.yaml'
        print()
        with open(configfile, 'r') as handle:
            configs = yaml.load(handle)
            df_fast = shootouts.preprocess(configs, best='time')
            df_small = shootouts.preprocess(configs, best='codesize')
            languages = configs.get('languages')
            for lang in languages:

                # TODO --
                #       print stddev
                #       print values that went into computation
                print('{0}-fast:'.format(lang))
                df_fast_filtered = df_fast.loc[df_fast.lang.isin([lang])]

                df_fast_filtered = df_fast.loc[df_fast.lang.isin([lang])]

                for lang, group in df_fast_filtered.groupby('lang'):
                    width = shootouts.gstddev(group.codesize.values.tolist())
                    height = shootouts.gstddev(group.time.values.tolist())
                    print('  gstddev(codesize): {0}'.format(width))
                    print('  stddev(codesize) : {0}'.format(group.codesize.std()))
                    print('  gstddev(time)    : {0}'.format(height))
                    print('  stddev(time)     : {0}'.format(group.time.std()))
                    print('  data:')
                    for s, c, t in zip(group.shootout, group.codesize, group.time):
                        print('    {0:20}: {1:8.5} : {2:8.5}'.format(s, c, t))

                print('{0}-small:'.format(lang))
                df_small_filtered = df_small.loc[df_small.lang.isin([lang])]
                for lang, group in df_small_filtered.groupby('lang'):
                    width = shootouts.gstddev(group.codesize.values.tolist())
                    height = shootouts.gstddev(group.time.values.tolist())
                    print('  gstddev(codesize): {0}'.format(width))
                    print('  stddev(codesize) : {0}'.format(group.codesize.std()))
                    print('  gstddev(time)    : {0}'.format(height))
                    print('  stddev(time)     : {0}'.format(group.time.std()))
                    print('  data:')
                    print('    {0:20}: {1:8} : {2:8}'.format('shootout', 'codesize', 'time'))
                    for s, c, t in zip(group.shootout, group.codesize, group.time):
                        print('    {0:20}: {1:8.5} : {2:8.5}'.format(s, c, t))



if __name__ == '__main__':
    unittest.main()

