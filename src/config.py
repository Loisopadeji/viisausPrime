"""
config.py
---------
All the settings that control how the app looks and where it finds data.

Keeping these in one place means you only edit here if a colour or a file
path ever changes, instead of hunting through every file in the project.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------------
# IMPORTANT FOR DEPLOYMENT:
# We never write a path like "C:/Users/Lois/Desktop/data.csv" because that
# folder does not exist on Streamlit's servers. Instead we work out where this
# file lives and build the path from there. This works on your laptop AND in
# the cloud, with no changes.

# Path(__file__) is this config.py file.
# .resolve() turns it into a full path.
# .parent is the "src" folder, and .parent again is the project root folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Now point at the data folder inside the project root.
DATA_PATH = PROJECT_ROOT / "data" / "viisaus_operations_data.csv"


# ---------------------------------------------------------------------------
# BRAND COLOURS (taken directly from the Viisaus presentation)
# ---------------------------------------------------------------------------
CREAM = "#FDF6EE"      # page background
OFFWHITE = "#FFFDF8"   # cards and panels
NAVY = "#292C35"       # headings and dark panels
GRAY = "#3E4044"       # body text
RED = "#DA3231"        # accent, key figures, highlights
LINE = "#E8DFD3"       # hairline borders and gridlines
MUTED = "#B9B2A8"      # secondary/comparison series in charts

# A reusable colour list for charts that need several series at once.
CHART_SEQUENCE = [NAVY, RED, MUTED, GRAY]


# ---------------------------------------------------------------------------
# APP TEXT
# ---------------------------------------------------------------------------
APP_NAME = "ViisausPrime"
APP_TAGLINE = "Predictive business intelligence for internal Operations"

# The forecast horizon we present to leadership.
FORECAST_MONTHS = 3
FORECAST_LABELS = ["Jan 2026", "Feb 2026", "Mar 2026"]
