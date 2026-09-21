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
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "viisaus_operations_data.csv"

# ---------------------------------------------------------------------------
# BRAND COLOURS (taken directly from the Viisaus presentation)
# ---------------------------------------------------------------------------
CREAM = "#FDFCFA"      # page background (near-white)
OFFWHITE = "#FFFDF8"   # cards and panels
NAVY = "#292C35"       # headings and dark panels
GRAY = "#3E4044"       # body text
RED = "#DA3231"        # accent, key figures, highlights
LINE = "#E8DFD3"       # hairline borders and gridlines
MUTED = "#B9B2A8"      # secondary/comparison series in charts

CHART_SEQUENCE = [NAVY, RED, MUTED, GRAY]

# ---------------------------------------------------------------------------
# APP TEXT
# ---------------------------------------------------------------------------
APP_NAME = "ViisausPrime"
APP_TAGLINE = "Predictive business intelligence for internal Operations"

FORECAST_MONTHS = 3
FORECAST_LABELS = ["Jan 2026", "Feb 2026", "Mar 2026"]

# ---------------------------------------------------------------------------
# TYPOGRAPHY
# ---------------------------------------------------------------------------
FONT_URL = (
    "https://fonts.googleapis.com/css2?family=Carlito:wght@400;700"
    "&family=Source+Sans+3:wght@400;600;700&display=swap"
)
FONT_STACK = "'Carlito', 'Calibri', 'Source Sans 3', 'Segoe UI', sans-serif"

# ---------------------------------------------------------------------------
# AUTHOR
# ---------------------------------------------------------------------------
AUTHOR = "Lois Opadeji"
LINKEDIN_URL = "https://www.linkedin.com/in/loisopadeji"
GITHUB_URL = "https://github.com/Loisopadeji"
