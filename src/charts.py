"""
charts.py
---------
Chart-building helpers, all styled in the Viisaus brand colours.

Keeping chart styling in one file means every chart in the app looks like it
belongs to the same family, and you only change a colour in one place.
"""

import plotly.graph_objects as go

from src.config import CREAM, GRAY, LINE, NAVY, RED


def _base_layout(fig, title, x_title, y_title, height=420):
    """
    Apply the shared Viisaus styling to any chart.

    Every chart gets a title, labelled axes with units, a transparent
    background so it sits naturally on the cream page, and soft gridlines.
    """
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=NAVY, family="Georgia, serif")),
        xaxis_title=x_title,
        yaxis_title=y_title,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=GRAY, family="Helvetica, Arial, sans-serif", size=12),
        height=height,
        margin=dict(l=60, r=30, t=60, b=60),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE)
    return fig


def forecast_line_chart(hist_x, hist_y, fc_x, fc_y, lower=None, upper=None,
                        title="", y_title="", hist_name="Actual", fc_name="Forecast"):
    """
    A line chart showing history in navy and the forecast in red, with an
    optional shaded confidence band.

    The colour split is deliberate: a viewer should be able to tell at a
    glance where measured fact ends and prediction begins.
    """
    fig = go.Figure()

    # Shaded confidence band, drawn first so the lines sit on top of it.
    if lower is not None and upper is not None:
        fig.add_trace(go.Scatter(
            x=list(fc_x) + list(fc_x)[::-1],
            y=list(upper) + list(lower)[::-1],
            fill="toself",
            fillcolor="rgba(218, 50, 49, 0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="95% confidence range",
        ))

    fig.add_trace(go.Scatter(
        x=hist_x, y=hist_y, mode="lines+markers", name=hist_name,
        line=dict(color=NAVY, width=2.5), marker=dict(size=5),
    ))

    # Join the forecast to the last actual point so the line is continuous.
    bridge_x = [list(hist_x)[-1]] + list(fc_x)
    bridge_y = [list(hist_y)[-1]] + list(fc_y)
    fig.add_trace(go.Scatter(
        x=bridge_x, y=bridge_y, mode="lines+markers", name=fc_name,
        line=dict(color=RED, width=3, dash="solid"), marker=dict(size=7),
    ))

    return _base_layout(fig, title, "Month", y_title)


def horizontal_bar(labels, values, title="", x_title="", colors=None, height=380):
    """A horizontal bar chart, useful for ranking sectors or risk factors."""
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors if colors else NAVY),
        text=[f"{v:,.0f}" if v >= 10 else f"{v:.2f}" for v in values],
        textposition="outside",
        textfont=dict(color=NAVY, size=11),
    ))
    fig = _base_layout(fig, title, x_title, "", height=height)
    fig.update_layout(showlegend=False)
    return fig


def grouped_bar(categories, series_a, series_b, name_a, name_b,
                title="", y_title="", height=380):
    """
    Two bars side by side per category. Used for model comparisons, where
    seeing the selected model next to the alternative is the whole point.
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(name=name_a, x=categories, y=series_a, marker_color=RED))
    fig.add_trace(go.Bar(name=name_b, x=categories, y=series_b, marker_color="#B9B2A8"))
    fig.update_layout(barmode="group")
    return _base_layout(fig, title, "", y_title, height=height)


def donut(labels, values, title="", height=380):
    """A donut chart for showing how a total splits across categories."""
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=[NAVY, RED, "#5A5E६8".replace("६", "6"), "#B9B2A8",
                            "#8C8F98", "#C9BEB0", "#6B6E76"]),
        textinfo="label+percent", textfont=dict(size=11),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=NAVY, family="Georgia, serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=GRAY, size=12),
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )
    return fig
