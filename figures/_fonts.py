"""Register Liberation Serif for matplotlib if it is available.

The published figures use Liberation Serif (metric-compatible with Times).
Set LIBERATION_FONT_DIR to a folder containing LiberationSerif*.ttf, or
install the font system-wide. Without it, matplotlib falls back to its
default serif font and the figures differ only in typeface.
"""
import glob, os
import matplotlib.font_manager as fm

_dirs = [os.environ.get("LIBERATION_FONT_DIR", ""),
         os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")]
for _d in _dirs:
    if _d:
        for _f in glob.glob(os.path.join(_d, "**", "LiberationSerif*.ttf"), recursive=True):
            fm.fontManager.addfont(_f)
