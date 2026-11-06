#!/bin/bash
set -u
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
jobs() {
  for era in 2014 2018 2022; do
    for horizon in H1H HDA; do
      for learner in L1 L2; do
        if [ "$era" = "2014" ] && [ "$learner" = "L1" ]; then continue; fi
        echo "$era $horizon $learner"
      done
    done
    echo "$era - L3"
  done
}
run_one() {
  era=$1; horizon=$2; learner=$3
  if [ "$learner" = "L3" ]; then
    $PY job_fit.py --era "$era" --learner L3 > "logs/stdout_${era}_L3.txt" 2>&1
  else
    $PY job_fit.py --era "$era" --horizon "$horizon" --learner "$learner" \
      > "logs/stdout_${era}_${horizon}_${learner}.txt" 2>&1
  fi
  echo "done: $era $horizon $learner (exit $?)"
}
export -f run_one
export PY
jobs | xargs -P 2 -L 1 bash -c 'run_one "$@"' _
echo "REST DONE"
