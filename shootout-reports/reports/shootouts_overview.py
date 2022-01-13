#!/usr/bin/env python3
# encoding: utf-8

"""shootouts-overview

This is a temporary copy of shootouts.py with some modifications to display
an overview of CLBG plots with lines by language.

Eventually, let's refactor the original shootouts.py to handle this 'special'
case as well as the other plots.

Do a 'diff' of the two files to see the 'patch'.


"""

# Standard library imports
import collections
import itertools
import math
import os

# External imports
try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import matplotlib.lines as mlines
    import numpy as np
    import pandas as pd
    import yaml
    from scipy.stats.mstats import gmean
except ImportError:
    print('Required modules not installed')
    print('Try `pip3 install -r requirements.txt`')
    raise ImportError


## Global configurations
pd.options.mode.chained_assignment = None  # default='warn'
plt.rcParams.update({'figure.max_open_warning': 0}) # Suppress warning

# Default global colormap for common langs
COLORMAP = {
            'chapel':'#00ff00',
            'gcc':'#000000',
            'gpp':'#808080',
            'go':'#00ffff',
            'java':'#5382A1',
            'python3':'#ffff00',
            'rust':'#8B4513',
            'scala':'#E5554D',
            'swift':'#FFA970',
            'ifc': '#C7B991'
            }


def getconfigs(configfile):
    """Parse configfile into configs object"""
    configs = yaml.load(open(configfile, 'r'))

    # Location of pulled data
    if 'data' not in configs.keys():
        configs['data'] = 'benchmarksgame/website/websites/u64q/data/data.csv'

    return configs


def mergecolormap(colormap):
    """Merge/overwrite default colormap with new colormap"""
    # Default colormap
    global COLORMAP

    # Update COLORMAP from configs
    if colormap:
        for key, value in colormap.items():
            COLORMAP[key] = value
    return COLORMAP


def gstddev(v):
    """Geometric standard deviation"""
    if type(v) is list:
        v = np.array(v)
    u = gmean(v)
    s = 0
    for i in range(len(v)):
        s += np.power(np.log(v[i]/u), 2)
    s = s/len(v)
    return np.exp(s)


def drop(df, truthtable):
    """Gather and drop all row indices for this truth table"""
    indices = df.loc[truthtable].index.values.tolist()
    return df.drop(indices)


def dropworst(df, criterion):
    """Drop all rows that are not best of a given criteria, within a language
       e.g. criteria = 'time_s_' will result in dropping all but the fastest
       shootout implementations per language.
    """
    for shootout in df.shootout.unique():
        for lang in df.lang.unique():
            # Truth table for all rows with this shootout && lang
            tt = (df.shootout == shootout) & (df.lang == lang)
            # Gather all row indices for this truth table
            indices = df.loc[tt].index.values.tolist()
            if len(indices) > 1:
                # Find the minimum value for
                idxmin = df.loc[tt, criterion].idxmin()
                indices.remove(idxmin)
                df = df.drop(indices)
    return df


def dropblacklist(df, blacklist):
    """Drop blacklisted rows from dataframe"""
    if type(blacklist) is not dict:
        return df

    for language, shootouts in blacklist.items():
        if type(shootouts) is dict:
             for shootout, IDs in shootouts.items():
                if type(IDs) is list:
                    # Remove IDs for this benchmark for this language
                    for ID in IDs:
                        df = drop(df, (df.shootout == shootout) & (df.lang == language) & (df.id == ID))
                elif type(IDs) is int:
                    # Remove ID for this benchmark for this language
                    ID = IDs
                    df = drop(df, (df.shootout == shootout) & (df.lang == language) & (df.id == ID))
                else:
                    # Remove benchmark for this language from dataframe
                    df = drop(df, (df.shootout == shootout) & (df.lang == language))
        else:
            # Remove language from dataframe
            df = drop(df, df.lang == language)
    return df


def preprocess(configs, best=None):
    """Modify df directly parsed from CVS repo
       'best' is criteria for how to choose the best data point for multiple
       implementations
    """

    df = pd.read_csv(configs['data'])

    # Enables convience accessors, e.g. dfsub.cpu_s_
    df.columns = [c.replace('(', '_') for c in df.columns]
    df.columns = [c.replace(')', '_') for c in df.columns]

    df = df.rename(index=str, columns={'name':'shootout', 'size_B_': 'codesize_B_', 'elapsed_s_': 'time_s_'})

    # Drop NaN rows for shootout name and elapsed time
    df.dropna(inplace=True)

    # Drop rows with no time data or failed runs
    df = df.query('time_s_ != 0')
    df = df.query('status == 0')

    # Drop useless columns
    df = df.drop('n', 1)
    df = df.drop('status', 1)
    df = df.drop('load', 1)
    df = df.drop('cpu_s_', 1)


    # Add relative data columns
    df['codesize'] = np.nan
    df['time'] = np.nan
    df['time_codesize'] =(df.time_s_ * df.codesize_B_)

    main = configs.get('main', None)
    if main is None:
        print("Configs Error: 'main' must be defined")
        return
    mainlanguage = main.get('language', None)
    if mainlanguage is None:
        print("Configs Error: 'main['language']' must be defined")
        return
    languages = configs.get('languages', None)
    if mainlanguage not in languages:
        print("Configs Error: 'main['language']' must be contained in languages")
        return

    reference = configs.get('reference', None)
    if reference == 'languages':
        #print('Scaling values to minimum of selected languages')
        df = df.loc[df.lang.isin(languages)]


    # Populate relative data columns
    size_mins = {}
    time_mins = {}
    time_codesize_mins = {}
    for shootout in df.shootout.unique():

        size_mins[shootout] = df.ix[df.shootout == shootout, 'codesize_B_'].min()
        df.ix[df.shootout==shootout, 'codesize'] = df.ix[df.shootout==shootout, 'codesize_B_']/size_mins[shootout]

        time_mins[shootout] = df.ix[df.shootout == shootout, 'time_s_'].min()
        df.ix[df.shootout==shootout, 'time'] = df.ix[df.shootout==shootout, 'time_s_']/time_mins[shootout]

        time_codesize_mins[shootout] = df.ix[df.shootout == shootout, 'time_codesize'].min()
        df.ix[df.shootout==shootout, 'time_codesize'] = df.ix[df.shootout==shootout, 'time_codesize']/time_codesize_mins[shootout]


    # Drop languages not selected
    if type(languages) is list:
        df = df.loc[df.lang.isin(languages)]

    # Drop blacklisted rows
    blacklist = configs.get('blacklist', None)
    df = dropblacklist(df, blacklist)


    # Drop all but best rows for a given language/benchmark (where 'best' is a column defined by argument)
    if best is not None:
        df = dropworst(df, best)

    # Drop duplicates, which are created if a data point fits 'best' for both definitions of 'best'
    df.drop_duplicates(inplace=True)

    return df


def draw_ellipse(x, y, width, height, ax, color):
    """Draw an ellipse based on mean / stddev"""
    ell = mpl.patches.Ellipse((x, y), width=width, height=height, color=color)
    ell.set_alpha(0.1)

    # Draw the ellipse
    ax.add_artist(ell)


def colorwheel(items):
    """Build colormap from list of items distributed over colorwheel"""
    if len(items) > 3:
        spectrum = [x%1 for x in np.linspace(0.4, 1.25, len(items))]
    else:
        spectrum = [x%1 for x in np.linspace(0.4, 0.9, len(items))]

    colors = [plt.cm.hsv(i) for i in spectrum]
    return {l: c for (l, c) in zip(items, colors)}


def buildlegend(ax, kwargs, langs):
    """Build the ax.legend"""
    # Temporarily hard-coded...

    print(langs)
    # TODO - this should be controlled by a separate options
    #if 'values' in kwargs['display']:

    # List of legend objects
    handles = []

    # Colors
    colormap = kwargs['langcolormap']
    for lang in langs:
        handles.append(mpl.patches.Patch(color=colormap[lang], label=lang))

    # Shapes
    #for dflabel, marker in zip(kwargs['dflabels'], kwargs['dfmarkers']):
    #    handles.append(mpl.lines.Line2D([], [], color='none', marker=marker, markersize=8, label=dflabel))
    if 'means' in kwargs['display']:
        for dflabel, marker in zip(kwargs['dflabels'], kwargs['dfmarkers']):
            handles.append(mpl.lines.Line2D([], [], color='none', marker=marker, markersize=14, label='mean-'+dflabel))
    if 'gmeans' in kwargs['display']:
        for dflabel, marker in zip(kwargs['dflabels'], kwargs['dfmarkers']):
            handles.append(mpl.lines.Line2D([], [], color='none', marker=marker, markersize=14, label='gmean-'+dflabel))

    ax.legend(handles=handles, numpoints=1, loc=1, fancybox=True, framealpha=0.5, labelspacing=0.6)
    #else:
    #    ax.legend(numpoints=1, loc=1, fancybox=True, framealpha=0.5, labelspacing=0.6)


def defaultmarkers(dfs, display):
    """Get the default markers"""
    markers = ['s', 'o']
    # Special case for plotting just the means of 1 dataframe
    if len(dfs) == 1 and ('means' in display or 'gmeans' in display) and 'values' not in display:
            markers = ['*']
    return markers


def defaultlabels(dfs, display):
    """Get the default labels"""
    if len(dfs) > 1:
        labels = [str(i) for i in range(len(dfs))]
    else:
        labels = ['']
    return labels


def plotlanguages(dfs, **kwargs):
    """Plot all shootouts

    df: dataframe || [dataframe,] - benchmark data, after being preprocessed

    Plot Options
    ------------
    x = 'codesize'        - column from df to plot on x-axis
    y = 'time'            - column from df to plot on y-axis
    display = ['values',] - What to display in plotting, can be:
                              'values' - data point per benchmark per language
                              'means'  - large avg data point per language
                              'stddev' - standard deviation ellipse per mean
                              'lines'  - lines between corresponding points, e.g. fastest vs smallest

    Display Options
    ---------------
    dflabels         - list of labels associated with list of dataframes
    dfmarkers        - markers to denote dataframes
    xlabel = 'relative source size'
    ylabel = 'relative execution time'
    name: string     - Plot title name
    ymax: real       - max y value, defaults to auto-scale
    xmax: real       - max x value, defaults to auto-scale
    log = False      - Log scale for y-axis, adds log() around ylabel
    colormap: dict   - {lang: color, ...}

    Other Options
    -------------
    save: string     - Save plot output to this path

    """

    if type(dfs) is list:
        langs = set()
        for df in dfs:
            langs = langs.union(set(df.lang.unique()))
        langs = np.sort(list(langs))
    else:
        langs = np.sort(dfs.lang.unique())
        dfs = [dfs]

    display = kwargs.get('display', ['values'])
    kwargs['display'] = display
    dfmarkers = kwargs.get('dfmarkers', defaultmarkers(dfs, display))
    kwargs['dfmarkers'] = dfmarkers

    colormap = mergecolormap(kwargs.get('colormap', None))
    kwargs['langcolormap'] = colormap

    # Use Pandas style of plots
    plt.rcParams.update(pd.tools.plotting.mpl_stylesheet)

    # Create figure and axis
    fig, ax = plt.subplots()

    # Figure settings
    fig.set_size_inches(18.5, 10.5)

    log = kwargs.get('log', False)
    # Draw lines
    if len(dfs) == 2:
        for lg1, lg2 in zip(dfs[0].groupby('lang'), dfs[1].groupby('lang')):
            lang1, group1 = lg1
            lang2, group2 = lg2
            if lang1 != lang2:
                print('langs did not match:', lang1,', ', lang2)
            color = colormap[lang1]
            # Draw lines
            x1, y1 = gmean(group1.codesize.values.tolist()), gmean(group1.time.values.tolist())
            x2, y2 = gmean(group2.codesize.values.tolist()), gmean(group2.time.values.tolist())
            l = mlines.Line2D([x1,x2], [y1, y2], color=color, linestyle='--')
            ax.add_line(l)
            #plt.plot(x1, y1, x2, y2, marker='o', ms=8, color=color, linestyle='--')


    for i, dfplot in enumerate(dfs):
        # Actual plotting
        for lang, group in dfplot.groupby('lang'):
            marker = dfmarkers[i]
            color = colormap[lang]

            if 'values' in display:
                ax.plot(group.codesize, group.time, marker=marker, linestyle='', ms=8, label=lang, color=color)

            if 'means' in display:
                xy = (group.codesize.mean(), group.time.mean())

                #if lines and type(dfs) is list:
                #    # draw lines between all points within this group
                #    all_data = zip(group.codesize, group.time)
                #    plt.plot(
                #        *zip(*itertools.chain.from_iterable(itertools.combinations(all_data, 2))),
                #              color=color, marker=marker, ms=8, label=lang, linestyle='--')
                #else:
                #    ax.plot(group.codesize, group.time, marker=marker, linestyle='', ms=8, label=lang, color=color)

                ax.plot(xy[0], xy[1], marker=marker, ms=14, c=color, label=lang)
            if 'gmeans' in display:
                xy = (gmean(group.codesize.values.tolist()), gmean(group.time.values.tolist()))
                ax.plot(xy[0], xy[1], marker=marker, ms=14, c=color, label=lang)

            if 'gstddev' in display:
                draw_ellipse(x=gmean(group.codesize.values.tolist()), y=gmean(group.time.values.tolist()),
                             width=gstddev(group.codesize.values.tolist())*2, height=gstddev(group.time.values.tolist())*2,
                             ax=ax, color=color)

            if 'stddev' in display:
                if log:
                    print('Warning: Log + stddev option are not compatible')
                draw_ellipse(x=group.codesize.mean(), y=group.time.mean(),
                             width=group.codesize.std()*2, height=group.time.std()*2,
                             ax=ax, color=color)

    dflabels = kwargs.get('dflabels', defaultlabels(dfs, display))
    kwargs['dflabels'] = dflabels

    buildlegend(ax, kwargs, langs)

    name = kwargs.get('name', 'shootouts')
    ax.set_title(name)

    xlabel = kwargs.get('xlabel', 'relative source size')
    ax.set_xlabel(xlabel)

    ylabel = kwargs.get('ylabel', 'relative execution time')
    if log:
        ylabel = 'log({0})'.format(ylabel)
    ax.set_ylabel(ylabel)

    # Auto-scaling
    ax.relim()
    ax.autoscale_view()

    ymax = kwargs.get('ymax', None)
    if ymax is not None:
        ax.set_ylim(ymax=ymax)
    xmax = kwargs.get('xmax', None)
    if xmax is not None:
        ax.set_xlim(xmax=xmax)

    ax.margins(0.075)
    ax.set_yscale('linear')
    ax.set_ylim(ymin=0.9)
    ax.set_xlim(xmin=0.97)
    if log:
        ax.set_yscale('log')



    # Save the plot
    save = kwargs.get('save', None)
    if save is not None:
        if not os.path.exists(save):
            os.makedirs(save)
        plt.savefig(os.path.join(save, name+'.png'), bbox_inches='tight')
    else:
        # Show the plot
        plt.show()


def plotshootout(dfs, **kwargs):
    """Plot shootout from dataframe

    dfs            - dataframe or list of dataframes, can compare up to 2 at a time.
    log = True     -
    display = []   - What to display in plotting, can be:
                        'lines'  - lines between corresponding points if 2 df are passed
    save: str      -
    colormap: dict -
    name: str      -
    """

    if type(dfs) is list:
        df = pd.concat(dfs)
    else:
        df = dfs

    name = kwargs.get('name', '-'.join(df.shootout.unique()))
    langs = np.sort(df.lang.unique())

    ## Plotting

    # Use Pandas style of plots
    plt.rcParams.update(pd.tools.plotting.mpl_stylesheet)
    colormap = mergecolormap(kwargs.get('colormap', None))

    # Create figure and axis
    fig, ax = plt.subplots()

    # Figure settings
    fig.set_size_inches(18.5, 10.5)

    marker = 'o'
    display = kwargs.get('display', ['values'])
    lines = 'lines' in display

    groups = df.groupby('lang')

    # Actual plotting
    for lang, group in groups:
        color = colormap[lang]
        if lines and type(dfs) is list:
            # draw lines between all points within this group
            all_data = zip(group.codesize, group.time)
            plt.plot(
                *zip(*itertools.chain.from_iterable(itertools.combinations(all_data, 2))),
                      color=color, marker=marker, ms=8, label=lang, linestyle='--')
        else:
            ax.plot(group.codesize, group.time, marker=marker, linestyle='', ms=8, label=lang, color=color)


    log = kwargs.get('log', True)

    # Axis settings
    ax.legend(numpoints=1, loc='upper right', fancybox=True, framealpha=0.5)
    ax.set_title(name)

    xlabel = kwargs.get('xlabel', 'relative source size')
    ax.set_xlabel(xlabel)

    ylabel = kwargs.get('ylabel', 'relative execution time')
    if log:
        ylabel = 'log({0})'.format(ylabel)
    ax.set_ylabel(ylabel)

    # recompute the ax.dataLim
    ax.relim()
    ax.autoscale_view()
    ax.margins(0.075) # Optional, just adds 5% padding to the autoscaling

    if log:
        ax.set_yscale('log')
        ax.set_ylim(ymin=0.9)
    else:
        ax.set_yscale('linear')
        ax.autoscale_view()

    save = kwargs.get('save', None)
    if save is not None:
        if not os.path.exists(save):
            os.makedirs(save)
        plt.savefig(os.path.join(save, name+'.png'), bbox_inches='tight')
    else:
        plt.show()

    return


##
## Language Overview
##
def language_overview(configs, save=None):
    """
    """

    df = pd.read_csv(configs['data'])
    df_small = preprocess(configs, best='codesize')
    df_fast = preprocess(configs, best='time')

    plotlanguages(df_small, log=True, save=save, name='geometric-means-shootouts-smallest', display=['gmeans'], xmax=4.0, ymax=250)
    plotlanguages(df_fast, log=True, save=save, name='geometric-means-shootouts-fastest', display=['gmeans'], xmax=4.0, ymax=250)


##
## Languages
##

def language_all(configs, save=None):
    df = pd.read_csv(configs['data'])
    df_fast = preprocess(configs, best='time')
    df_small = preprocess(configs, best='codesize')
    dfs = [df_fast, df_small]
    languages = configs.get('languages')
    mainlanguage = configs.get('main').get('language')
    # Language head to heads

    xmax=9
    ymax=25

    # Filter down to just the 2 languages
    main_fast = df_fast.loc[df_fast.lang.isin([mainlanguage])]
    main_small = df_small.loc[df_small.lang.isin([mainlanguage])]
    # Plot main language alone
    plotlanguages([main_small, main_fast],
                  display=['gmeans', 'gstddev', 'values'],
                  name=mainlanguage, xmax=xmax, ymax=ymax, save=save,
                  dfmarkers=['s', 'o'], dflabels=['smallest', 'fastest'])

    # Collect Outliers
    df_fast_outliers = set(drop(df_fast, df_fast.time < ymax).lang.unique())
    df_small_outliers = set(drop(df_small, df_small.time < ymax).lang.unique())

    df_outliers = df_fast_outliers.union(df_small_outliers)

    for lang in [x for x in languages if x != mainlanguage]:

        # Filter down to just the 2 languages
        df_fast_filtered = df_fast.loc[df_fast.lang.isin([lang, mainlanguage])]
        df_small_filtered = df_small.loc[df_small.lang.isin([lang, mainlanguage])]


        # Plot!
        plotlanguages([df_small_filtered, df_fast_filtered],
                      display=['gmeans', 'gstddev', 'values'],
                      name=mainlanguage+'-'+lang, xmax=xmax, ymax=ymax, save=save,
                      dfmarkers=['s', 'o'], dflabels=['smallest', 'fastest'])

        # Special cases that have outliers outside of the standard range
        if lang in df_outliers:
            plotlanguages([df_small_filtered, df_fast_filtered],
                          display=['gmeans', 'gstddev', 'values'],
                          name=mainlanguage+'-'+lang+'-full', xmax=xmax, ymax=None, save=save,
                          dfmarkers=['s', 'o'], dflabels=['smallest', 'fastest'])


##
## Shootouts
##

def shootout_all(configs, save=None):
    # Parse fastest and smallest, append data sets
    df = pd.read_csv(configs['data'])
    df_fast = preprocess(configs, best='time')
    df_small = preprocess(configs, best='codesize')

    # Shootouts overview
    for shootout in df_fast.shootout.unique():
        df_fast_shootout = df_fast.loc[df_fast.shootout.isin([shootout])]
        df_small_shootout = df_small.loc[df_small.shootout.isin([shootout])]

        plotshootout([df_fast_shootout, df_small_shootout], display=['lines'],
                      save=save)


#
# Experimental Features
#

def table(df):
    """Generate table of relative time, codesize, and time*codesize"""
    shootouts = df.groupby('shootout')
    for key, shootout in shootouts:
        shootout.sort_values('time', inplace=True)
        print()
        print(shootout)


def barplot(df, save=None):
    """ Bar graph:     Language - avg(relative performance / bytes of source code)

        - Add a new column, relative performance / bytes of source code (perf_per_byte)
        - Compute averages
        - Plot as bar graph
    """
    # Create new dataframe for stats
    dfstats = pd.DataFrame(index=df.lang.unique(), columns=['mean', 'min', 'max'])#, 'time_codesize_min', 'time_codesize_max', 'time_codesize_mean'])

    groups = df.groupby('lang')

    for key, group in groups:
        dfstats.set_value(key, 'mean', group.time_codesize.mean())
        dfstats.set_value(key, 'min', group.time_codesize.min())
        dfstats.set_value(key, 'max', group.time_codesize.max())
        #dfstats.ix[dfstats.lang==key].time_codesize_mean = group.time_codesize.mean()

    dfstats.sort_values('mean', inplace=True)
    print(dfstats)

    # Create figure and axis
    fig, ax = plt.subplots()

    # Figure settings
    fig.set_size_inches(18.5, 10.5)

    width=0.35
    ind = np.arange(len(dfstats['mean']))
    yerr=[dfstats['mean'] - dfstats['min'], dfstats['max'] - dfstats['mean']]
    ax.bar(ind, dfstats['mean'], width=width, ecolor='g')
    ax.set_ylabel('Mean relative time*codesize')
    #ax.set_title('')
    ax.set_xticks(ind + width)
    ax.set_xticklabels(dfstats.index)

    plt.show()

def language_lines(configs, save=None):
    df = pd.read_csv(configs['data'])
    df_fast = preprocess(configs, best='time')
    df_small = preprocess(configs, best='codesize')

    plotlanguages([df_small, df_fast],dflabels=['smallest', 'fastest'], log=False, save=save, name='zoomed-out', display=['gmeans'], xmax=3.5, ymax=100)

    # Filter out python3 for zoomed in graph
    languages = configs.get('languages')
    if 'python3' in languages:
        print('python3 found in config - removing for zoomed-in lines plot...')
        languages.remove('python3')
        df_small = df_small.loc[df_small.lang.isin(languages)]
        df_fast = df_fast.loc[df_fast.lang.isin(languages)]

        plotlanguages([df_small, df_fast],dflabels=['smallest', 'fastest'], log=False, save=save, name='zoomed-in', display=['gmeans'], xmax=3.5, ymax=12)
