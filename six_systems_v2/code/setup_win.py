"""A9 data setup on the compute machine: EIA-930 six-month files from eia.gov and the archived
GEFS control extracts from the public repository. Downloads use the system curl."""
import os, subprocess, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
def fetch(url, path):
    subprocess.run(["curl.exe", "-sSfL", "--retry", "5", "-o", path + ".part", url], check=True); os.replace(path + ".part", path)
os.makedirs(os.path.join(HERE, "raw_eia"), exist_ok=True); os.makedirs(os.path.join(HERE, "gefs", "raw_ctl"), exist_ok=True)
files = ["2015_Jul_Dec"] + [f"{y}_{h}" for y in range(2016, 2026) for h in ["Jan_Jun", "Jul_Dec"]] + ["2026_Jan_Jun"]
for f in files:
    p = os.path.join(HERE, "raw_eia", f"EIA930_BALANCE_{f}.csv")
    if not os.path.exists(p):
        fetch(f"https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_{f}.csv", p)
    print("EIA", f, os.path.getsize(p) // 1_000_000, "MB", flush=True)
gz = os.path.join(HERE, "gefs_ctl_footprint_points.csv.gz")
if not os.path.exists(gz):
    fetch("https://github.com/DresdenGman/PJM-Cold-Calibration-Benchmark/raw/main/forecast_weather_a8/data/gefs_ctl_footprint_points.csv.gz", gz)
d = pd.read_csv(gz, compression="gzip")
for c, g in d.groupby("cycle"):
    g.to_csv(os.path.join(HERE, "gefs", "raw_ctl", f"{c}.csv"), index=False)
print("GEFS seeded", d.cycle.nunique(), "SETUP DONE", flush=True)
