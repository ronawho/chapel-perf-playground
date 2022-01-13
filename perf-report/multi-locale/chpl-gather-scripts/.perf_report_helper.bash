generateMultiLocalePerfReport () {
  # Copy the overlays and make chapel
  cd $CHPL_HOME/ && \
  git co . && \
  cp -r  ~/Desktop/chapel/chapel-code/perf-report-overlays/multi-locale/* . && \
  git apply util/gengraphs.diff && \
  cp -r ~/Desktop/chapel/chapel-code/perf-report-overlays/util/* util/ && \
  make -j && \
  #
  # generate the combined .dat, .pdf etc files (removing the old onces first)
  rm -f ~/Desktop/chapel/chapel-perf/perf-report/multi-locale/graphs/* && \
  export CHPL_TEST_UTIL_DIR=$CHPL_HOME/util/ && \
  ./util/perf/create_graphs.py -c util/perf/multi-locale-graphs.yaml -d ~/Desktop/chapel/chapel-perf/perf-report/multi-locale/ && \
  #
  # copy the files to the multi-locale perf report, rename, and add xworse stuff
  cd ~/Desktop/chapel/chapel-docs/whitewedding/MS10/perf-report/multi-locale/ && \
  rm *.pdf *.dat *.fixed *.log
  cp -r ~/Desktop/chapel/chapel-perf/perf-report/multi-locale/graphs/* . && \
  ./rename.sh && \ 
  BIGGER_IS_BETTER=True  python xworse.py *.dat && \
  BIGGER_IS_BETTER=False python xworse.py SSCA2-22-4.dat lulesh-dense.dat miniMD.dat isx-release.dat mg.dat && \
  # 
  # generate the pdf report (run pdflatex a bunch of times to correctly gen the
  # index/table. 2 times is probably enough, but I'm paranoid at this point)
  cd ../  && \
  pdflatex -interaction nonstopmode all-files.tex || pdflatex -interaction nonstopmode all-files.tex || pdflatex -interaction nonstopmode all-files.tex || pdflatex -interaction nonstopmode all-files.tex
  rm -f all-files.aux all-files.log all-files.toc all-files.out
}
