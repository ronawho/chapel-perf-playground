export VALID_CHPL_CONFIGS=(GasnetMpi GasnetAries Ugni)

checkConfig() {
  check_config=${1}
  for config in ${VALID_CHPL_CONFIGS[@]}; do
    if [ ${check_config} == ${config} ]; then
      return 0
    fi
  done
  echo "Config '${check_config}' is not supported, valid options are '${VALID_CHPL_CONFIGS[*]}'"
  exit
}

setExtra () {
  unset CHPL_GMP
  unset CHPL_REGEXP
}

setNoExtra () {
  export CHPL_GMP=none
  export CHPL_REGEXP=none
}

unsetComm () {
  unset CHPL_COMM
  unset CHPL_COMM_SUBSTRATE
  unset CHPL_COMM_SEGMENT
  unset CHPL_CONFIG_NAME
  module unload craype-hugepages16M
}

helpSetUgni () {
  export CHPL_COMM=ugni
  module load craype-hugepages16M
}

setUgni () {
  helpSetUgni
  export CHPL_TASKS=qthreads
  export CHPL_CONFIG_NAME=ugni
}

unsetUgni () {
  unsetComm
  module unload craype-hugepages16M
}

helpSetGasnet () {
  unsetUgni
  export CHPL_COMM=gasnet
}

setGasnetAries () {
  helpSetGasnet
  export CHPL_COMM_SUBSTRATE=aries
  export CHPL_CONFIG_NAME=gn-aries
}

setGasnetMpi () {
  helpSetGasnet
  export CHPL_COMM_SUBSTRATE=mpi
  export GASNET_QUIET=Y
  export MPICH_GNI_DYNAMIC_CONN=disabled
  export CHPL_CONFIG_NAME=gn-mpi
}

unsetGasnet() {
  unsetComm
}

setCommNone() {
  unsetComm
  export CHPL_COMM=none
}

setPerfdat() {
  chpl_short_version=`chpl --version | head -n1 | cut -f3 -d " " | cut -f 1,2 -d "."`
  export CHPL_TEST_PERF_DIR=${LUS_HOME}/perfdat/${chpl_short_version}/${CHPL_CONFIG_NAME}
}
