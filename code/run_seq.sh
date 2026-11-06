#!/bin/bash
# Sequential driver (v2.1 run): one job at a time. Parallel launches were
# abandoned after OpenMP thread thrash on this 4-core VM collapsed
# throughput (see run notes); jobs run with capped, passive-wait threads.
set -u
cd "$(dirname "$0")"
export OMP_NUM_THREADS=2
export OMP_WAIT_POLICY=PASSIVE
export GOMP_SPINCOUNT=0
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
PY=${PYTHON:-python3}

run_job() {
  era=$1; horizon=$2; learner=$3
  echo "=== start $era $horizon $learner $(date +%H:%M:%S)"
  if [ "$learner" = "L3" ]; then
    $PY job_fit.py --era "$era" --learner L3 > "logs/stdout_${era}_L3.txt" 2>&1
  else
    $PY job_fit.py --era "$era" --horizon "$horizon" --learner "$learner" \
      > "logs/stdout_${era}_${horizon}_${learner}.txt" 2>&1
  fi
  echo "done: $era $horizon $learner (exit $?) $(date +%H:%M:%S)"
}

# fast cells first (pipeline validation), L1 (slow HistGBR) last
for era in 2014 2018 2022; do run_job $era - L3; done
for era in 2014 2018 2022; do
  run_job $era H1H L2
  run_job $era HDA L2
done
for era in 2018 2022 2014; do
  run_job $era H1H L1
  run_job $era HDA L1
done

echo "=== phase2 $(date +%H:%M:%S)"
$PY phase2_loeo.py > logs/phase2_loeo.log 2>&1
echo "done: phase2 (exit $?)"
echo "=== report $(date +%H:%M:%S)"
$PY report.py > logs/report.log 2>&1
echo "done: report (exit $?)"
echo "ALL DONE $(date +%H:%M:%S)"
