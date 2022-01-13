This directory contains performance results from 16 nodes of an XC (jupiter)

Rough specs: 28 core (56HT) Broadwell w/ 128GB ram per node

Chapel performance numbers are gathered using the benchmarks and start_test
from the latest release across multiple Chapel versions. Basically we checkout
the repo and overlay for the latest release, setup things for the current
comm/tasking config, load the appropriate Chapel module, and run the tests.

chpl-gather-scripts contains the scripts that I used to gather the 1.19 chapel
numbers on jupiter. They probably won't work out of the box for future
releases, but it's a good starting point.

The reference number gathering is less automated. The chapel-benchmarks repo
has READMEs/scripts/HOWTOs to help.
