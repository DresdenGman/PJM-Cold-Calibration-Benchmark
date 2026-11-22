#!/bin/bash
set -u
cd "$(dirname "$0")"
export OMP_NUM_THREADS=2 OMP_WAIT_POLICY=PASSIVE GOMP_SPINCOUNT=0 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=${PY:-python3}
for era in 2014 2018 2022; do
  for horizon in HDA H1H; do
    for learner in L1 L2; do
      echo "=== MW $era $horizon $learner $(date +%H:%M:%S)"
      $PY job_mw.py --era $era --horizon $horizon --learner $learner > "logs/stdout_mw_${era}_${horizon}_${learner}.txt" 2>&1
    done
  done
  echo "=== MW $era L3 $(date +%H:%M:%S)"
  $PY job_mw.py --era $era --learner L3 > "logs/stdout_mw_${era}_L3.txt" 2>&1
done
echo "MW_ALL_DONE $(date +%H:%M:%S)"
