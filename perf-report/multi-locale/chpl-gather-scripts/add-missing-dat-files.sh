# The scripts expect every dir to have a file for each .dat file. Copy the
# header for any .dat file that is missing from dirs (using the latest ugni
# folder as the directory that should have all of them)
latest_ver=1.19
best_config=ugni
vers=(1.17 1.18 1.19)
configs=(gn-aries gn-mpi ugni)

for f in $latest_ver/$best_config/*.dat; do
  for ver in ${vers[@]}; do 
    for config in ${configs[@]}; do
      base=$(basename $f)
      other_f="$ver/$config/$base"
      if [ ! -f "$other_f" ]; then
        echo "$other_f is missing"
        head -n1 $f > $other_f
      fi
    done
  done

  base=$(basename $f)
  other_f="references/$base"
  if [ ! -f "$other_f" ]; then
    echo "$other_f is missing"
    head -n1 $f > $other_f
  fi
done
