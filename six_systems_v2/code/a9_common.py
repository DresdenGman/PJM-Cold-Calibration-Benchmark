"""A9 shared setup: repository code, events, eras, populations."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(HERE), "repo")
sys.path.insert(0, os.path.join(REPO, "code"))
OLD_EVENTS = {
    "pjm": {"2014": dict(name="event_2014_vortex", start="2014-01-06 00:00", end="2014-01-09 00:00"),
            "2018": dict(name="event_2018_snap", start="2017-12-28 00:00", end="2018-01-08 00:00"),
            "2022": dict(name="event_2022_elliott", start="2022-12-23 00:00", end="2022-12-27 00:00")},
    "miso": {"2018": dict(name="event_2018_snap", start="2017-12-28 00:00", end="2018-01-08 00:00"),
             "2019": dict(name="event_2019_vortex", start="2019-01-29 00:00", end="2019-02-01 00:00"),
             "2022": dict(name="event_2022_elliott", start="2022-12-23 00:00", end="2022-12-27 00:00")}}
def events(system):
    ev = dict(OLD_EVENTS[system])
    ev.update(json.load(open(os.path.join(REPO, "extended_events_a6", "populations", system, "events_a6.json"))))
    return ev
EVAL = {"2014": ("2013-12-01", "2014-02-28"), "2018": ("2017-12-01", "2018-02-28"), "2019": ("2018-12-01", "2019-02-28"),
        "2022": ("2022-12-01", "2023-02-28"), "2024": ("2023-12-01", "2024-02-29"), "2025": ("2024-12-01", "2025-02-28"),
        "2026": ("2025-12-01", "2026-02-28")}
ERAS = {"pjm": ["2014", "2018", "2019", "2022", "2024", "2025", "2026"], "miso": ["2018", "2019", "2022", "2024", "2025", "2026"]}
BA = {"pjm": ("PJM", 170000.0), "miso": ("MISO", 150000.0)}

# ---------------- A11: four further balancing authorities (PLAN_A11.md)
A11_SYS = {"ercot": ("ERCO", 120000.0, 0), "spp": ("SWPP", 90000.0, 15), "nyiso": ("NYIS", 45000.0, 30), "isone": ("ISNE", 40000.0, 45)}
for _s, (_ba, _gl, _off) in A11_SYS.items():
    BA[_s] = (_ba, _gl)
A11_ERAS = [str(y) for y in range(2018, 2027)]          # January year of the evaluation winter
def eval_span(system, era):
    if system in A11_SYS:
        y = int(era); return (f"{y-1}-12-01", f"{y}-02-29" if y % 4 == 0 else f"{y}-02-28")
    return EVAL[era]
def gefs_cols(system):
    if system in A11_SYS:
        o = A11_SYS[system][2]; return [f"p{i}" for i in range(o, o + 15)]
    return [f"p{i}" for i in (range(15) if system == "pjm" else range(15, 30))]
def gefs_dir(system):
    return os.path.join(os.path.dirname(HERE), "a11", "gefs", "raw_ctl") if system in A11_SYS else os.path.join(HERE, "gefs", "raw_ctl")
def era5_glob(system):
    return os.path.join(os.path.dirname(HERE), "a11", "era5", f"{system}_*.csv") if system in A11_SYS else os.path.join(HERE, "era5", f"{system}_*.csv")
SHED = {"ercot": ("2021-02-14", "2021-02-20"), "spp": ("2021-02-14", "2021-02-20")}   # local dates, flagged (PLAN_A11.md)
_events_old = events
def events(system):
    if system in A11_SYS:
        p = os.path.join(os.path.dirname(HERE), "a11", "populations", system, "events.json")
        return json.load(open(p))
    return _events_old(system)
