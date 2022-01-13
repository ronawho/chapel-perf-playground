Scripts used to gather multi-locale Chapel results for 1.19 perf report

Note that these scripts probably won't work from release to release without
being updated, and they might have some of my (Elliot) paths hard-coded in
them. They aren't perfect, but they're a good starting point for trying to
remember what has to be done to gather numbers.


Scripts for running on a local machine:
----------------------------------------
    gather-multi-loc-perf-rep-on-jupiter.sh

gather-multi-loc-perf-rep-on-jupiter.sh just ssh's to the machine that's doing
the tests and kicks off a test instance for a specific version/config.


Scripts for the machine running the jobs:
-----------------------------------------
    .setChplHelpers.bash
    .multiLocPerHelpers.bash

.setChplHelpers.bash is a generic helper file I use for Crays. It has simple
functions like setUgniQthreads that sets CHPL_COMM=ugni, CHPL_TASKS=qthreads,
and loads an appropriate hugepage module.

.multiLocPerHelpers.bash has functions to clone the latest repo, build
test-venv, fixup some benchmarks that didn't work with older compilers, load an
appropriate compiler/Chapel module, select specific nodes, and actually run the
tests

The most annoying and manual part of this entire process is updating
.multiLocPerHelpers.bash to deal with backwards incompatible changes.


Scripts used to gen the multi-locale graphs from the data:
----------------------------------------------------------
    .perf_report_helper.bash

.perf_report_helper.bash is an absolutely awful script I use to generate the
individual graphs and to generate the perf-report pdf. It's seriously the worst
and has lots of hard-coded paths for where my various repos live, but again
it's a good starting point for what has to be done to gen the graphs.
