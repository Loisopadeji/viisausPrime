"""
data.py
-------
Everything to do with loading and reshaping the operations dataset.

Why this is a separate file: every page of the app needs the same data.
Rather than loading it five times, we load it once here and let every page
import it. Streamlit's cache makes sure the work only happens once.
"""

import pandas as pd
import streamlit as st

from src.config import DATA_PATH


# @st.cache_data tells Streamlit: "run this function once, then remember the
# answer". Without it, the CSV would be re-read every time a user clicks
# anything, which makes the app feel slow.
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Read the operations CSV and convert the date columns into real dates.

    Returns a pandas DataFrame with one row per project.
    """
    df = pd.read_csv(DATA_PATH)

    # Pandas reads dates as plain text by default. We convert them so we can
    # do date maths later (for example, "which month did this project start?").
    for col in ["start_date", "planned_end_date", "actual_end_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


@st.cache_data
def get_revenue_series() -> pd.DataFrame:
    """
    Build a monthly revenue history for the whole firm.

    Business rule: revenue is booked in the month a project STARTS.
    Cancelled projects are excluded because they were signed but never
    delivered, so they never produced revenue. Including them would make
    every forecast too optimistic.
    """
    df = load_data()

    # Keep everything except cancelled work.
    active = df[df["status"] != "Cancelled"].copy()

    # Create a "month" column, e.g. 2025-03, from the start date.
    active["month"] = active["start_date"].dt.to_period("M").dt.to_timestamp()

    # Add up contract value within each month.
    monthly = (
        active.groupby("month", as_index=False)["contract_value_ngn"]
        .sum()
        .sort_values("month")
        .reset_index(drop=True)
    )
    monthly = monthly.rename(columns={"contract_value_ngn": "revenue_ngn"})

    return monthly


@st.cache_data
def get_revenue_by_sector() -> pd.DataFrame:
    """Same as above, but split out by each of the seven sectors."""
    df = load_data()
    active = df[df["status"] != "Cancelled"].copy()
    active["month"] = active["start_date"].dt.to_period("M").dt.to_timestamp()

    by_sector = (
        active.groupby(["month", "sector"], as_index=False)["contract_value_ngn"]
        .sum()
        .rename(columns={"contract_value_ngn": "revenue_ngn"})
    )
    return by_sector


@st.cache_data
def get_staffing_series() -> pd.DataFrame:
    """
    Build a monthly staffing demand history.

    This is the key difference from revenue. Revenue lands in one month, but
    a consultant stays assigned for the WHOLE life of a project. So we cannot
    simply count start months.

    Instead we "explode" every project into one row per month it was active,
    then add up team sizes within each month. That gives a true picture of how
    many consultant seats were occupied at any point in time.
    """
    df = load_data()
    active = df[df["status"] != "Cancelled"].copy()

    rows = []
    for _, project in active.iterrows():
        # If a project finished, use the actual end date. If it is still
        # running, use the planned end date instead.
        end = project["actual_end_date"]
        if pd.isna(end):
            end = project["planned_end_date"]
        if pd.isna(project["start_date"]) or pd.isna(end):
            continue

        # Build the list of months this project spanned.
        months = pd.period_range(
            project["start_date"].to_period("M"),
            end.to_period("M"),
            freq="M",
        )
        for m in months:
            rows.append(
                {
                    "month": m.to_timestamp(),
                    "sector": project["sector"],
                    "team_size": project["team_size"],
                }
            )

    panel = pd.DataFrame(rows)

    # Total consultants engaged per month across the firm.
    monthly = (
        panel.groupby("month", as_index=False)["team_size"]
        .sum()
        .sort_values("month")
        .reset_index(drop=True)
    )
    monthly = monthly.rename(columns={"team_size": "consultants"})

    # Trim to the reporting window so early partial months do not distort it.
    monthly = monthly[monthly["month"] <= "2025-12-01"].reset_index(drop=True)

    return monthly


@st.cache_data
def get_staffing_by_sector() -> pd.DataFrame:
    """Monthly staffing demand, split by sector."""
    df = load_data()
    active = df[df["status"] != "Cancelled"].copy()

    rows = []
    for _, project in active.iterrows():
        end = project["actual_end_date"]
        if pd.isna(end):
            end = project["planned_end_date"]
        if pd.isna(project["start_date"]) or pd.isna(end):
            continue
        months = pd.period_range(
            project["start_date"].to_period("M"), end.to_period("M"), freq="M"
        )
        for m in months:
            rows.append(
                {
                    "month": m.to_timestamp(),
                    "sector": project["sector"],
                    "team_size": project["team_size"],
                }
            )

    panel = pd.DataFrame(rows)
    by_sector = (
        panel.groupby(["month", "sector"], as_index=False)["team_size"]
        .sum()
        .rename(columns={"team_size": "consultants"})
    )
    by_sector = by_sector[by_sector["month"] <= "2025-12-01"]
    return by_sector


def format_naira(value: float) -> str:
    """
    Turn a big number into something readable for a CEO.

    Example: 7_784_092_410 becomes "NGN 7.78B".
    """
    if value >= 1_000_000_000:
        return f"NGN {value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"NGN {value / 1_000_000:.1f}M"
    return f"NGN {value:,.0f}"
