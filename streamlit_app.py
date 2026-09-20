"""
===========================================================================
 ViisausPrime
 Predictive business intelligence for internal Operations
===========================================================================

This is the MAIN FILE. When Streamlit starts your app, this is the file it
runs, top to bottom, every time someone interacts with the page.

HOW THE APP IS ORGANISED
------------------------
  streamlit_app.py   <- you are here: layout, navigation, and all the pages
  src/config.py      <- colours, file paths, app name
  src/data.py        <- loading and reshaping the operations data
  src/models.py      <- the four predictive models
  src/charts.py      <- chart styling helpers
  data/              <- the operations dataset (CSV)

HOW NAVIGATION WORKS
--------------------
The sidebar holds a radio button list. Whichever option is selected decides
which block of code runs further down. It is a simple if/elif chain, which is
the easiest pattern to read and debug when you are starting out.
"""

import pandas as pd
import streamlit as st

from src.config import (
    APP_NAME, APP_TAGLINE, CREAM, GRAY, LINE, NAVY, OFFWHITE, RED,
)
from src.data import (
    format_naira, get_revenue_by_sector, get_staffing_by_sector, load_data,
)
from src.models import (
    forecast_revenue, forecast_staffing, score_client_renewal, score_delivery_risk,
)
from src.charts import forecast_line_chart, grouped_bar, horizontal_bar


# ===========================================================================
# PAGE SETUP
# This must be the FIRST Streamlit command in the file, or Streamlit errors.
# ===========================================================================
st.set_page_config(
    page_title=f"{APP_NAME} | Viisaus Technology",
    page_icon="📊",
    layout="wide",                    # use the full browser width
    initial_sidebar_state="expanded", # sidebar open when the CEO arrives
)


# ===========================================================================
# STYLING
# Streamlit's default look is grey and generic. This CSS block applies the
# Viisaus brand so the app matches the presentation.
# ===========================================================================
st.markdown(f"""
<style>
    .stApp {{ background-color: {CREAM}; }}
    section[data-testid="stSidebar"] {{ background-color: {NAVY}; }}
    section[data-testid="stSidebar"] * {{ color: {CREAM} !important; }}

    h1, h2, h3 {{ color: {NAVY} !important; font-family: Georgia, serif !important; }}
    p, li, div, span, label {{ color: {GRAY}; }}

    /* The big number cards at the top of pages */
    div[data-testid="stMetric"] {{
        background-color: {OFFWHITE};
        border: 1px solid {LINE};
        border-radius: 8px;
        padding: 16px 18px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    div[data-testid="stMetricValue"] {{
        color: {RED} !important;
        font-family: Georgia, serif !important;
        font-size: 26px !important;
    }}
    div[data-testid="stMetricLabel"] {{ color: {GRAY} !important; font-size: 13px !important; }}

    /* A reusable coloured note box */
    .insight {{
        background-color: {NAVY};
        color: {CREAM};
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.55;
        margin: 8px 0 16px 0;
    }}
    .insight b {{ color: {RED}; }}

    .footer {{
        color: #C9BEB0;
        font-size: 11px;
        border-top: 1px solid {LINE};
        padding-top: 10px;
        margin-top: 36px;
    }}
    #MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


def insight(text: str):
    """Shortcut for drawing the navy 'what this means' box."""
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)


def page_footer():
    """The branded footer line, shown at the bottom of every page."""
    st.markdown(
        f'<div class="footer">{APP_NAME} | {APP_TAGLINE}</div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# SIDEBAR NAVIGATION
# ===========================================================================
with st.sidebar:
    st.markdown(f"## {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.markdown("---")

    page = st.radio(
        "Navigate to",
        [
            "Executive Dashboard",
            "Revenue Forecast",
            "Staffing & Capacity",
            "Delivery Risk",
            "Client Renewal",
            "Data Explorer",
            "Methodology",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Viisaus Technology Limited")
    st.caption("Forecast period: Q1 2026")


# Load the dataset once. Because of caching in data.py, this is instant on
# every page after the first.
df = load_data()


# ===========================================================================
# PAGE 1: EXECUTIVE DASHBOARD
# The landing page. A CEO should understand the whole picture here without
# clicking anything.
# ===========================================================================
if page == "Executive Dashboard":
    st.title("Executive Dashboard")
    st.markdown(
        "Forward visibility across revenue, capacity, delivery and client retention, "
        "generated from the firm's own operational record."
    )

    # Run all four models.
    rev_hist, rev_fc, rev_meta = forecast_revenue()
    staff_hist, staff_fc, staff_meta, _ = forecast_staffing()
    risk_df, risk_meta = score_delivery_risk()
    renew_df, renew_meta = score_client_renewal()

    # --- The four headline numbers -------------------------------------
    q1_revenue = rev_fc["forecast_ngn"].sum()
    peak_staff = staff_fc["forecast"].max()
    high_risk = risk_df[risk_df["risk_score"] > 0.5]
    at_risk_value = high_risk["contract_value_ngn"].sum()
    watch_list = renew_df[renew_df["renewal_probability"] < 0.25]
    watch_clients = watch_list["client_id"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Q1 2026 Revenue Forecast", format_naira(q1_revenue))
    c2.metric("Peak Monthly Headcount", f"{peak_staff:,.0f}")
    c3.metric("Value at Delivery Risk", format_naira(at_risk_value))
    c4.metric("Priority Renewal Clients", f"{watch_clients}")

    st.markdown("")

    # --- Two headline charts side by side ------------------------------
    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            forecast_line_chart(
                rev_hist["month"], rev_hist["revenue_ngn"] / 1e9,
                rev_fc["month"], rev_fc["forecast_ngn"] / 1e9,
                rev_fc["lower_ngn"] / 1e9, rev_fc["upper_ngn"] / 1e9,
                title="Monthly Revenue: History and Q1 2026 Forecast",
                y_title="Revenue (NGN Billions)",
                hist_name="Actual revenue", fc_name="Forecast revenue",
            ),
            use_container_width=True,
        )

    with right:
        st.plotly_chart(
            forecast_line_chart(
                staff_hist["month"], staff_hist["consultants"],
                staff_fc["month"], staff_fc["forecast"],
                staff_fc["lower"], staff_fc["upper"],
                title="Monthly Staffing Demand: History and Q1 2026 Forecast",
                y_title="Consultants engaged",
                hist_name="Actual demand", fc_name="Forecast demand",
            ),
            use_container_width=True,
        )

    insight(
        f"<b>What this means:</b> The firm is forecast to earn "
        f"{format_naira(q1_revenue)} in Q1 2026 and will need up to "
        f"{peak_staff:,.0f} consultants at the quarter's peak. "
        f"{len(high_risk)} live projects carrying {format_naira(at_risk_value)} "
        f"show the same warning pattern as past overruns, and {watch_clients} "
        f"recent clients fall in the lowest renewal tier. All four figures are "
        f"produced by models validated on data they had never seen."
    )

    # --- Sector concentration ------------------------------------------
    st.subheader("Where the work is concentrated")
    sector_rev = (
        df[df["status"] != "Cancelled"]
        .groupby("sector", as_index=False)["contract_value_ngn"].sum()
        .sort_values("contract_value_ngn")
    )
    st.plotly_chart(
        horizontal_bar(
            sector_rev["sector"].tolist(),
            (sector_rev["contract_value_ngn"] / 1e6).round(0).tolist(),
            title="Total Contracted Revenue by Sector, 2021 to 2025",
            x_title="Revenue (NGN Millions)",
            height=400,
        ),
        use_container_width=True,
    )
    page_footer()


# ===========================================================================
# PAGE 2: REVENUE FORECAST
# ===========================================================================
elif page == "Revenue Forecast":
    st.title("Revenue Forecast")
    st.markdown("Where firm revenue is heading over the next quarter, and what drives it.")

    hist, fc, meta = forecast_revenue()

    c1, c2, c3 = st.columns(3)
    c1.metric("Q1 2026 Total Forecast", format_naira(fc["forecast_ngn"].sum()))
    c2.metric("Model Used", meta["model"])
    c3.metric("Holdout Error (MAPE)", f"{meta['mape']:.1f}%")

    st.plotly_chart(
        forecast_line_chart(
            hist["month"], hist["revenue_ngn"] / 1e9,
            fc["month"], fc["forecast_ngn"] / 1e9,
            fc["lower_ngn"] / 1e9, fc["upper_ngn"] / 1e9,
            title="Monthly Revenue: 60 Months of History and Q1 2026 Forecast",
            y_title="Revenue (NGN Billions)",
            hist_name="Actual revenue", fc_name="Forecast revenue",
        ),
        use_container_width=True,
    )

    st.subheader("Month-by-month forecast")
    display = fc.copy()
    display["Month"] = display["month"].dt.strftime("%B %Y")
    display["Forecast"] = display["forecast_ngn"].apply(format_naira)
    display["Lower bound (95%)"] = display["lower_ngn"].apply(format_naira)
    display["Upper bound (95%)"] = display["upper_ngn"].apply(format_naira)
    st.dataframe(
        display[["Month", "Forecast", "Lower bound (95%)", "Upper bound (95%)"]],
        use_container_width=True, hide_index=True,
    )

    insight(
        "<b>How to read the range:</b> The single forecast figure is the most "
        "likely outcome, but project revenue is naturally lumpy month to month. "
        "The shaded band shows where the actual result is expected to land 95 "
        "percent of the time. Plan against the range, not the midpoint alone."
    )

    # Sector view, with a filter so leadership can drill in.
    st.subheader("Revenue history by sector")
    sector_data = get_revenue_by_sector()
    chosen = st.multiselect(
        "Select sectors to compare",
        sorted(sector_data["sector"].unique()),
        default=["Technology and Innovation", "Climate and Carbon Markets"],
    )
    if chosen:
        import plotly.graph_objects as go
        fig = go.Figure()
        palette = [NAVY, RED, "#8C8F98", "#B9B2A8", "#6B6E76", "#C9BEB0", "#4A4D57"]
        for i, sec in enumerate(chosen):
            sub = sector_data[sector_data["sector"] == sec]
            fig.add_trace(go.Scatter(
                x=sub["month"], y=sub["revenue_ngn"] / 1e6,
                mode="lines", name=sec,
                line=dict(color=palette[i % len(palette)], width=2),
            ))
        fig.update_layout(
            title="Monthly Revenue by Sector",
            xaxis_title="Month", yaxis_title="Revenue (NGN Millions)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=GRAY, size=12), height=420,
            legend=dict(orientation="h", y=-0.25),
        )
        fig.update_yaxes(gridcolor=LINE)
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    page_footer()


# ===========================================================================
# PAGE 3: STAFFING AND CAPACITY
# ===========================================================================
elif page == "Staffing & Capacity":
    st.title("Staffing and Capacity")
    st.markdown("How many consultants the firm will need, and when the pressure peaks.")

    hist, fc, meta, importance = forecast_staffing()

    peak_row = fc.loc[fc["forecast"].idxmax()]
    current = hist["consultants"].iloc[-1]
    growth = (peak_row["forecast"] - current) / current * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peak Monthly Demand", f"{peak_row['forecast']:,.0f}")
    c2.metric("Peak Month", peak_row["month"].strftime("%B %Y"))
    c3.metric("Growth vs Dec 2025", f"+{growth:.0f}%")
    c4.metric("Holdout Error (MAPE)", f"{meta['mape']:.1f}%")

    st.plotly_chart(
        forecast_line_chart(
            hist["month"], hist["consultants"],
            fc["month"], fc["forecast"], fc["lower"], fc["upper"],
            title="Firm-Wide Monthly Capacity Demand: History and Q1 2026 Forecast",
            y_title="Consultants engaged",
            hist_name="Actual demand", fc_name="Forecast demand",
        ),
        use_container_width=True,
    )

    insight(
        f"<b>Planning implication:</b> Demand climbs through the quarter and peaks "
        f"in {peak_row['month'].strftime('%B %Y')} at roughly "
        f"{peak_row['forecast']:,.0f} consultants, about {growth:.0f} percent above "
        f"where December 2025 closed. Capacity should be secured before the peak "
        f"rather than in response to it."
    )

    left, right = st.columns(2)

    with left:
        st.subheader("What drives the forecast")
        nice_names = {
            "lag_1": "Demand last month", "lag_2": "Demand 2 months ago",
            "lag_3": "Demand 3 months ago", "roll_3": "Recent 3-month average",
            "month_num": "Month of year (seasonality)", "time_idx": "Long-run trend",
        }
        imp = importance.copy()
        imp["label"] = imp["feature"].map(nice_names)
        imp = imp.sort_values("importance")
        st.plotly_chart(
            horizontal_bar(
                imp["label"].tolist(), imp["importance"].round(3).tolist(),
                title="Signal Strength in the Staffing Model",
                x_title="Relative importance (0 to 1)", height=360,
            ),
            use_container_width=True,
        )

    with right:
        st.subheader("Current demand by sector")
        sec = get_staffing_by_sector()
        latest = sec[sec["month"] == sec["month"].max()].sort_values("consultants")
        st.plotly_chart(
            horizontal_bar(
                latest["sector"].tolist(), latest["consultants"].tolist(),
                title="Consultants Engaged by Sector, December 2025",
                x_title="Consultants engaged", height=360,
            ),
            use_container_width=True,
        )

    page_footer()


# ===========================================================================
# PAGE 4: DELIVERY RISK
# ===========================================================================
elif page == "Delivery Risk":
    st.title("Delivery Risk")
    st.markdown(
        "Every ongoing project scored for the likelihood of overrunning its timeline, "
        "using only information known on day one."
    )

    risk_df, meta = score_delivery_risk()

    threshold = st.slider(
        "Risk threshold for flagging a project",
        min_value=0.30, max_value=0.80, value=0.50, step=0.05,
        help="Raise the threshold for a shorter, higher-confidence list. "
             "Lower it to catch more potential overruns at the cost of more false alarms.",
    )

    flagged = risk_df[risk_df["risk_score"] >= threshold]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projects Flagged", f"{len(flagged)} / {len(risk_df)}")
    c2.metric("Contract Value at Risk", format_naira(flagged["contract_value_ngn"].sum()))
    c3.metric("Historical Overrun Rate", f"{meta['overrun_rate']:.1f}%")
    c4.metric("Model Ranking Accuracy", f"{meta['auc']:.2f} AUC")

    insight(
        f"<b>How to use this:</b> The value shown is not expected loss. It is the "
        f"contract value sitting in projects that resemble past overruns and therefore "
        f"warrant a closer look. Work down the ranked list from the top, since the "
        f"highest-scoring projects carry both the clearest warning signs and much of "
        f"the value."
    )

    st.subheader(f"Ranked watch list, {len(flagged)} projects at or above {threshold:.0%}")
    table = flagged[[
        "project_id", "sector", "complexity", "team_size",
        "contract_value_ngn", "risk_score",
    ]].copy()
    table.columns = [
        "Project ID", "Sector", "Complexity", "Team Size",
        "Contract Value (NGN)", "Risk Score",
    ]
    table["Contract Value (NGN)"] = table["Contract Value (NGN)"].apply(lambda v: f"{v:,.0f}")
    table["Risk Score"] = table["Risk Score"].apply(lambda v: f"{v:.0%}")
    st.dataframe(table, use_container_width=True, hide_index=True, height=380)

    # Let leadership export the list for a delivery review meeting.
    st.download_button(
        "Download this watch list as CSV",
        data=flagged.to_csv(index=False).encode("utf-8"),
        file_name="delivery_risk_watchlist.csv",
        mime="text/csv",
    )

    st.subheader("Risk concentration by sector")
    by_sector = (
        flagged.groupby("sector", as_index=False)["contract_value_ngn"]
        .sum().sort_values("contract_value_ngn")
    )
    if not by_sector.empty:
        st.plotly_chart(
            horizontal_bar(
                by_sector["sector"].tolist(),
                (by_sector["contract_value_ngn"] / 1e6).round(0).tolist(),
                title="Flagged Contract Value by Sector",
                x_title="Contract value at risk (NGN Millions)", height=360,
            ),
            use_container_width=True,
        )
    page_footer()


# ===========================================================================
# PAGE 5: CLIENT RENEWAL
# ===========================================================================
elif page == "Client Renewal":
    st.title("Client Renewal")
    st.markdown(
        "Recently completed engagements scored for the likelihood the client returns "
        "within twelve months."
    )

    renew_df, meta = score_client_renewal()

    tier = st.slider(
        "Priority tier cut-off",
        min_value=0.10, max_value=0.50, value=0.25, step=0.05,
        help="Clients scoring below this are the priority group for proactive outreach.",
    )
    priority = renew_df[renew_df["renewal_probability"] < tier]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Priority Clients", f"{priority['client_id'].nunique()}")
    c2.metric("Relationship Value", format_naira(priority["contract_value_ngn"].sum()))
    c3.metric("Base Renewal Rate", f"{meta['renewal_rate']:.0f}%")
    c4.metric("Model Ranking Accuracy", f"{meta['auc']:.2f} AUC")

    insight(
        f"<b>Context that matters:</b> Only {meta['renewal_rate']:.0f} percent of clients "
        f"renew without active management, so renewal is earned rather than automatic. "
        f"A low score is not a lost client. It marks a relationship that will not renew "
        f"passively and is therefore worth a deliberate conversation now."
    )

    st.subheader(f"Priority outreach list, {len(priority)} engagements below {tier:.0%}")
    table = priority[[
        "client_name", "sector", "contract_value_ngn",
        "client_satisfaction_score", "delay_days", "renewal_probability",
    ]].copy()
    table.columns = [
        "Client", "Sector", "Contract Value (NGN)",
        "Satisfaction (1-5)", "Days Late", "Renewal Probability",
    ]
    table["Contract Value (NGN)"] = table["Contract Value (NGN)"].apply(lambda v: f"{v:,.0f}")
    table["Renewal Probability"] = table["Renewal Probability"].apply(lambda v: f"{v:.0%}")
    st.dataframe(table, use_container_width=True, hide_index=True, height=380)

    st.download_button(
        "Download this outreach list as CSV",
        data=priority.to_csv(index=False).encode("utf-8"),
        file_name="client_renewal_priority_list.csv",
        mime="text/csv",
    )

    st.subheader("Satisfaction is the strongest lever")
    scored = renew_df.copy()
    scored["band"] = pd.cut(
        scored["client_satisfaction_score"],
        bins=[0, 2, 3, 4, 5],
        labels=["1.0 to 2.0", "2.0 to 3.0", "3.0 to 4.0", "4.0 to 5.0"],
    )
    banded = scored.groupby("band", observed=True)["renewal_probability"].mean().reset_index()
    st.plotly_chart(
        horizontal_bar(
            banded["band"].astype(str).tolist(),
            (banded["renewal_probability"] * 100).round(1).tolist(),
            title="Average Predicted Renewal Probability by Satisfaction Band",
            x_title="Predicted renewal probability (%)", height=340,
        ),
        use_container_width=True,
    )
    page_footer()


# ===========================================================================
# PAGE 6: DATA EXPLORER
# Lets anyone check the underlying records for themselves, which is the
# fastest way to build trust in a model's output.
# ===========================================================================
elif page == "Data Explorer":
    st.title("Data Explorer")
    st.markdown("The full operational record behind every forecast and score on this app.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Projects", f"{len(df):,}")
    c2.metric("Sectors Covered", f"{df['sector'].nunique()}")
    c3.metric("Months of History", "60")

    st.subheader("Filter the records")
    f1, f2, f3 = st.columns(3)
    with f1:
        sectors = st.multiselect("Sector", sorted(df["sector"].unique()))
    with f2:
        statuses = st.multiselect("Status", sorted(df["status"].unique()))
    with f3:
        complexities = st.multiselect("Complexity", ["Low", "Medium", "High"])

    filtered = df.copy()
    if sectors:
        filtered = filtered[filtered["sector"].isin(sectors)]
    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    if complexities:
        filtered = filtered[filtered["complexity"].isin(complexities)]

    st.caption(f"Showing {len(filtered):,} of {len(df):,} projects")

    show = filtered[[
        "project_id", "sector", "service_line", "start_date", "status",
        "complexity", "team_size", "contract_value_ngn", "client_satisfaction_score",
    ]].copy()
    show["start_date"] = show["start_date"].dt.strftime("%b %Y")
    show.columns = [
        "Project ID", "Sector", "Service Line", "Start", "Status",
        "Complexity", "Team Size", "Contract Value (NGN)", "Satisfaction",
    ]
    st.dataframe(show, use_container_width=True, hide_index=True, height=420)

    st.download_button(
        "Download filtered data as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="viisaus_filtered_projects.csv",
        mime="text/csv",
    )
    page_footer()


# ===========================================================================
# PAGE 7: METHODOLOGY
# The page that answers "how do I know these numbers are real?"
# ===========================================================================
elif page == "Methodology":
    st.title("Methodology")
    st.markdown(
        "How each model was built, tested and selected. Every figure in this app comes "
        "from a model that was benchmarked against a simpler alternative and scored on "
        "data it had never seen during training."
    )

    st.subheader("Model selection results")
    results = pd.DataFrame({
        "Model": ["Revenue forecast", "Staffing forecast", "Delivery risk", "Client renewal"],
        "Question": [
            "What will the firm earn next quarter?",
            "How many consultants will be needed?",
            "Which live projects are likely to slip?",
            "Which clients are unlikely to return?",
        ],
        "Primary Metric": [
            "MAPE (lower is better)", "MAPE (lower is better)",
            "ROC-AUC (higher is better)", "ROC-AUC (higher is better)",
        ],
        "Selected Model": [
            "SARIMAX", "Gradient Boosting", "Logistic Regression", "Logistic Regression",
        ],
    })
    st.dataframe(results, use_container_width=True, hide_index=True)

    insight(
        "<b>Why four different winners:</b> Forecasting a number that trends upward is "
        "a fundamentally different problem from predicting a yes or no outcome. Rather "
        "than forcing one technique onto every question, each model was chosen by "
        "testing it against a simpler benchmark and keeping whichever performed better "
        "on unseen data. On two of the four questions the simpler model won, and it was "
        "kept."
    )

    st.subheader("The five-stage pipeline")
    stages = pd.DataFrame({
        "Stage": ["1. Data Sources", "2. Feature Engineering", "3. Training and Benchmarking",
                  "4. Validation", "5. Deployment"],
        "Scale": ["1,897 records", "Up to 12 features", "4 models, 2 candidates each",
                  "12 to 333 records held out", "190 + 547 scored"],
        "What happens": [
            "60 months, 7 sectors, 19 structured fields from project, finance and client systems",
            "45 cancelled projects excluded; lags, seasonality and business signals engineered",
            "Every model trained alongside a simpler benchmark under identical conditions",
            "Accuracy measured only on data withheld from training; the holdout selects the winner",
            "Ongoing projects and recent clients scored; forecasts refreshed on a monthly cycle",
        ],
    })
    st.dataframe(stages, use_container_width=True, hide_index=True)

    st.subheader("Guarding against data leakage")
    st.markdown("""
    **Leakage** happens when a model accidentally learns from information that would
    not be available at the moment the prediction is needed. It produces impressive
    test scores and useless real-world performance. Two deliberate rules prevent it here:

    - **The delivery risk model** scores projects on day one, so it may only use day-one
      facts: sector, complexity, team size and staffing mix. Actual delay, actual cost
      and client satisfaction are all excluded, because knowing them would mean already
      knowing the answer.
    - **The renewal model** runs at project close, so it is legitimately allowed to use
      how the project actually went. This is the opposite discipline, and it is correct
      because the prediction point is different.

    Time-series data is also never shuffled before splitting. Shuffling would let the
    model see future months while learning about the past, which flatters the score
    without improving the forecast.
    """)

    st.subheader("Known limitations")
    st.markdown("""
    - Accuracy figures are recalculated live from the loaded dataset and should be
      re-validated whenever the underlying data changes.
    - Forecasts extend three months. Error compounds with distance, so month three
      carries more uncertainty than month one. This is why every forecast shows a range.
    - The risk and renewal scores are prioritisation tools. They rank cases reliably
      but should not be treated as a final verdict on any single project or client.
    """)
    page_footer()
