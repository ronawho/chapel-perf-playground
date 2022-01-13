export LUS_HOME=/lus/scratch/eronagha

source ~/.setChplHelpers.bash

setupRepoPaths() {
  CHPL_VERSION_TO_TEST=${1:-''}
  CHPL_CONFIG_TO_TEST=${2:-''}

  if [ ${CHPL_VERSION_TO_TEST} != '' ] && [ ${CHPL_CONFIG_TO_TEST} != '' ]; then
    export CHPL_LANG_CLONED_HOME=${LUS_HOME}/chpl-multi-loc/${CHPL_VERSION_TO_TEST}/${CHPL_CONFIG_TO_TEST}/chapel
    export CHPL_CODE_CLONED_HOME=${LUS_HOME}/chpl-multi-loc/${CHPL_VERSION_TO_TEST}/${CHPL_CONFIG_TO_TEST}/chapel-code
  else
    export CHPL_LANG_CLONED_HOME=${LUS_HOME}/chapel
    export CHPL_CODE_CLONED_HOME=${LUS_HOME}/chapel-code
  fi
}

cloneOrCleanRepo() {
  DIR=${1}
  REPO=${2}
  BRANCH=${3}
  if [ -d ${DIR} ]; then
    cd ${DIR} && git clean -fdx . && git checkout .
  else
    git clone --depth=50 --branch=${BRANCH} $REPO ${DIR}
  fi
}

# Clone repos, copy overlay, build test-venv
setupRepos() {
  CUR_CHPL_TEST_VERSION=${1}

  cloneOrCleanRepo ${CHPL_LANG_CLONED_HOME} https://github.com/chapel-lang/chapel.git ${CUR_CHPL_TEST_VERSION}
  cloneOrCleanRepo ${CHPL_CODE_CLONED_HOME} https://stash.us.cray.com/scm/chapel/chapel-code.git ${CUR_CHPL_TEST_VERSION}

  export CHPL_TEST_UTIL_DIR=${CHPL_LANG_CLONED_HOME}/util
  export CHPL_TEST_VENV_DIR=`python ${CHPL_TEST_UTIL_DIR}/chplenv/chpl_home_utils.py --test-venv`

  export CHPL_PIP_INSTALL_PARAMS='-i http://slemaster.us.cray.com/pypi/simple --trusted-host slemaster.us.cray.com'
  cd ${CHPL_LANG_CLONED_HOME} && make test-venv
}

rmRepos() {
  mv ${LUS_HOME}/chpl-multi-loc/ ${LUS_HOME}/delete
  rm -rf ${LUS_HOME}/delete &
}

revertCommit() {
  commit_to_revert=${1}
  cd ${CHPL_LANG_CLONED_HOME}
  echo "Reverting ${commit_to_revert}"
  wget https://github.com/chapel-lang/chapel/commit/${commit_to_revert}.diff
  git apply --reverse -3 ${commit_to_revert}.diff
}

revertCommitReject() {
  commit_to_revert=${1}
  cd ${CHPL_LANG_CLONED_HOME}
  echo "Reverting ${commit_to_revert}"
  wget https://github.com/chapel-lang/chapel/commit/${commit_to_revert}.diff
  git apply --reverse --reject ${commit_to_revert}.diff
}

# in place sed (in case we're not using gsed and -i doesn't work)
mySed() {
  file=${1}
  search_text=${2}
  replace_text=${3}
  sed s/"${search_text}"/"${replace_text}"/g ${file} > ${file}.tmp  && mv ${file}.tmp ${file}
}

replaceInTests() {
  search_text="${1}"
  replace_text="${2}"
  echo "Replacing '${search_text}' with '${replace_text}' in tests"
  export -f mySed
  cd ${CHPL_LANG_CLONED_HOME}
  git grep --name-only "${search_text}" -- ${CHPL_LANG_CLONED_HOME}/test/*.chpl | xargs -I {} bash -c "mySed {} '${search_text}' '${replace_text}'"
}

removeUnorderedOps() {
  replaceInTests "use UnorderedAtomics;" "\/\/use UnorderedAtomics;"
  replaceInTests "unorderedAtomicFence();" ";\/\/unorderedAtomicFence();"
  replaceInTests "unorderedAdd" "add"
  replaceInTests "unorderedXor" "xor"

  replaceInTests "use UnorderedCopy;" "\/\/use UnorderedCopy;"
  replaceInTests "unorderedCopyFence();" ";\/\/unorderedCopyFence();"
  replaceInTests "unorderedCopy(" "__primitive(\"=\","
}

replaceUnorderedOps() {
  replaceInTests "use UnorderedAtomics;" "use BufferedAtomics;"
  replaceInTests "unorderedAtomicFence();" "flushAtomicBuff();"
  replaceInTests "unorderedAdd" "addBuff"
  replaceInTests "unorderedXor" "xorBuff"
  # TODO add fences at end of forall?

  replaceInTests "use UnorderedCopy;" "\/\/use UnorderedCopy;"
  replaceInTests "unorderedCopyFence();" ";\/\/unorderedCopyFence();"
  replaceInTests "unorderedCopy(" "__primitive(\"=\","
}

removeManaged() {
  replaceInTests "unmanaged" ""
  replaceInTests "owned" ""
}

removeOverride() {
  replaceInTests "override" ""
}

# revert "domain/range.member->contains" for ISx, SSCA, CoMD
replaceContains() {
  replaceInTests "myKeys.contains" "myKeys.member"
  replaceInTests "random_indices.contains" "random_indices.member"
  replaceInTests "wholeFluff.contains" "wholeFluff.member"
  replaceInTests "LocAccumStencilDom.contains" "LocAccumStencilDom.member"
  replaceInTests "myBlock.contains" "myBlock.member"
  replaceInTests "locDom.contains" "locDom.member"
  replaceInTests "targetLocDom.contains" "targetLocDom.member"
  replaceInTests "localDom.contains" "localDom.member"
  replaceInTests "locDom.myFluff.contains" "locDom.myFluff.member"
}

# remove -sParallelScan and --[no-]optimize-forall-unordered-ops
removeBadCompopts() {
  rm "${CHPL_LANG_CLONED_HOME}/test/scan/scanPerf.ml-compopts"
  rm "${CHPL_LANG_CLONED_HOME}/test/studies/bale/histogram/histo-atomics-forall-opt.ml-compopts"
  rm "${CHPL_LANG_CLONED_HOME}/test/studies/bale/indexgather/ig-forall-opt.ml-compopts"
}

fixBenchmarksFor117() {
  replaceContains
  removeUnorderedOps
  removeBadCompopts
  removeManaged
  removeOverride
}

fixBenchmarksFor118() {
  replaceContains
  replaceUnorderedOps
  removeBadCompopts
}

# update bin subdir
updateBinSubdir() {
  mySed "${CHPL_LANG_CLONED_HOME}/util/chplenv/chpl_bin_subdir.py" "return result" "return platform"
}

# Test a config for a given version of Chapel
testConfig() {

  CHPL_VERSION_TO_TEST=${1}
  CHPL_CONFIG_TO_TEST=${2}
  CHPL_TESTS_TO_TEST=${3}
  checkConfig ${CHPL_CONFIG_TO_TEST}

  # clone repos
  setupRepoPaths ${CHPL_VERSION_TO_TEST} ${CHPL_CONFIG_TO_TEST}
  setupRepos ${CHPL_TESTS_TO_TEST}

  # fix up some benchmarks so they work with older releases
  if [[ "${CHPL_VERSION_TO_TEST}" == "1.17"* ]]; then
    export CHPL_TEST_PERF_DATE="03/27/18"
    updateBinSubdir
    fixBenchmarksFor117
  elif [[ "${CHPL_VERSION_TO_TEST}" == "1.18"* ]]; then
    export CHPL_TEST_PERF_DATE="09/04/18"
    updateBinSubdir
    fixBenchmarksFor118
  elif [[ "${CHPL_VERSION_TO_TEST}" == "1.19"* ]]; then
    export CHPL_TEST_PERF_DATE="03/04/19"
  fi

 
  # grab broadwell nodes (likely to change over time)
  export CHPL_LAUNCHER_CONSTRAINT=BW28
  export CHPL_LAUNCHER_CORES_PER_LOCALE=56

  # load the current gnu target compiler
  source ${CHPL_CODE_CLONED_HOME}/build/functions.bash
  source ${CHPL_CODE_CLONED_HOME}/build/compiler_versions.bash
  load_target_compiler gnu

  # specify what config we want, and load chapel module -- relies on ~/.setChplHelpers
  set${CHPL_CONFIG_TO_TEST}
  module load chapel/${CHPL_VERSION_TO_TEST}
  setPerfdat

  # increase default timeout
  export CHPL_TEST_TIMEOUT=500

  # limit interference from concurrent runs
  export CHPL_TEST_LIMIT_RUNNING_EXECUTABLES=yes

  # test performance for current config
  cd ${CHPL_LANG_CLONED_HOME}/test/
  ${CHPL_LANG_CLONED_HOME}/util/start_test --performance --perflabel ml- --numtrials 3 .
  #${CHPL_LANG_CLONED_HOME}/util/start_test --performance --perflabel ml- --numtrials 1 npb/ep/mcahir/ep.chpl
}

