#!/bin/bash
# Full Run-1 driver: prep (already done separately) -> fit jobs -> LOEO -> report.
set -u
cd "$(dirname "$0")"
PY=${PYTHON:-python3}

jobs() {
  for era in 2014 2018 2022; do
    for horizon in H1H HDA; do
      for learner in L1 L2; do
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
$PY phase2_loeo.py > logs/stdout_phase2.txt 2>&1
echo "phase2 exit $?"
$PY report.py
echo "ALL DONE"
