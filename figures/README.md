# Figures

Scripts and plotted data for every figure in the manuscript and its supplement.
Each script reads only files in this folder (or the released results matrices)
and writes PDF and PNG next to itself.

| File | Figure | Script |
|---|---|---|
| `fig_headline` | Main text, coverage in six events (PJM and MISO) | `make_fig_headline.py ../code/results/results_matrix.csv ../replication_miso/results/results_matrix.csv fig_headline` |
| `fig0_design_schematic` | Main text, evaluation design | `make_fig_design.py fig0_design_schematic` |
| `fig6_event_series` | Main text, the 2014 vortex hour by hour | `build_figs_v3.py` |
| `fig3_frontier` | Main text, exceedance–headroom frontier | `build_figs_v3.py` |
| `fig2_transfer_illusion` | Main text, PJM transfer gaps | `build_figs_v3.py` |
| `fig5_operator_peaks` | Supplement, PJM operator peak errors | `build_figs_v3.py` |
| `fig1_collapse` | Supplement, collapse by learner (day-ahead) | `build_figs_v3.py` |
| `fig4_temp_reliability` | Supplement, coverage by temperature decile | `build_figs_v3.py` |
| `fig7_oracle_collapse` | Supplement, collapse gap on the one-hour oracle arm | `build_fig7_gap.py` |

`build_figs_v3.py` and `build_fig7_gap.py` read the CSVs in `data/` and check
them against `data/md5sums.txt` before plotting. `build_figs_v3.py` also writes
every plotted coordinate to `plotted_coords.json`.

Typeface: the published figures use Liberation Serif. Set `LIBERATION_FONT_DIR`
to a folder containing `LiberationSerif*.ttf` (or install the font); otherwise
matplotlib falls back to its default serif font.

Requirements: Python 3, numpy, pandas, matplotlib.
