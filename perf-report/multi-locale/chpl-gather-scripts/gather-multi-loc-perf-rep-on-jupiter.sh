#/usr/bin/env bash

export TEST_MACHINE=jupiter

function kill_current_jobs {
  echo "Killing jobs on ${TEST_MACHINE}"
  ssh ${TEST_MACHINE} "pkill -u ${USER}"
  exit
}

trap kill_current_jobs INT

versions=(1.17.1 1.18.0 1.19.0)
configs=(GasnetMpi GasnetAries Ugni)

scp .multiLocPerHelpers.bash $TEST_MACHINE:~/

for version in ${versions[@]}; do
  for config in ${configs[@]}; do
    echo "Testing ${version} ${config} on ${TEST_MACHINE}"
    ssh ${TEST_MACHINE} "source ~/.multiLocPerHelpers.bash && testConfig ${version} ${config} master" &
    sleep 1
  done
  ## only run one version at a time to limit how much we're hogging the system
  #wait
  sleep 300
done
wait

echo ""
echo "Done"
