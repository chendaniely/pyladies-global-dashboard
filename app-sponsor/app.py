# from io import StringIO
import requests

import numpy as np
import pandas as pd
from plotnine import (
    ggplot,
    aes,
    geom_bar,
    geom_col,
    geom_text,
    labs,
    coord_flip,
    scale_y_continuous,
    scale_fill_manual,
    theme_tufte,
    theme,
    element_blank,
    element_rect,
    element_text,
)
from shiny.express import ui, render

# Import Font Awesome
ui.head_content(
    ui.HTML("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """)
)

ui.tags.style("""
        .card-min-width {
            min-width: 160px;  /* Adjust as needed */
            word-break: break-word;
        }
    """)

# Download the JSON data
url = "https://portal.pyladies.com/stats.json"
response = requests.get(url)
data = response.json()
stats = data["stats"]

# Donation data
num_sponsors_committed = stats["sponsorship_committed_count"]
num_sponsors_contacted = stats["sponsorship_total_count"]
sponsorship_paid = float(stats["sponsorship_paid_amount"])
sponsorship_paid_num = stats["sponsorship_paid_count"]
sponsorship_pending = float(stats["sponsorship_pending_amount"])
sponsorship_pending_num = stats["sponsorship_pending_count"]
sponsorship_committed = float(stats["sponsorship_committed_amount"])
sponsorship_paid_pct = sponsorship_paid / sponsorship_committed * 100
goal = stats["sponsorship_goal"]
goal_pct = sponsorship_paid / goal

# csv_data_status = """status,count
# paid,18
# rejected,15
# awaiting response,31
# invoiced,1
# agreement signed,1
# agreement sent,2
# """

# sponsor_status = pd.read_csv(StringIO(csv_data_status))

sponsor_status = pd.DataFrame(
    stats["sponsorship_breakdown"][0]["data"], columns=["status", "count"]
)
sponsor_status = sponsor_status.assign(
    status=sponsor_status["status"].str.title().str.replace(" ", "\n")
)
sponsor_status["percent"] = (
    sponsor_status["count"] / sponsor_status["count"].sum() * 100
)


# csv_data_tier = """status,count
# booster,2
# champion,1
# connector,2
# individual,5
# partner,7
# supporter,5
# """

# sponsor_tier = pd.read_csv(StringIO(csv_data_tier))

sponsor_tier = pd.DataFrame(
    stats["sponsorship_breakdown"][1]["data"], columns=["tier", "count"]
)

sponsor_tier["percent"] = (
    sponsor_tier["count"] / sponsor_tier["count"].sum() * 100
)
sponsor_tier = sponsor_tier.assign(
    tier=sponsor_tier["tier"].str.title().str.replace(" ", "\n")
)

funding_goal = pd.DataFrame({
    "segment": ["goal", "stretch"],
    "amount": [
        int(goal),
        int(sponsorship_committed - goal),
    ],
})

# Make segment an ordered categorical so stacking is correct
funding_goal["segment"] = pd.Categorical(
    funding_goal["segment"],
    categories=["stretch", "goal"],
    ordered=True,
)

paid_funding = pd.DataFrame({
    "segment": ["paid", "total"],
    "amount": [
        sponsorship_paid,
        sponsorship_committed - sponsorship_paid,
    ],
})
# Make segment an ordered categorical so stacking is correct
paid_funding["segment"] = pd.Categorical(
    paid_funding["segment"],
    categories=["total", "paid"],
    ordered=True,
)


# begin app -----

# Page setup
ui.page_opts(title="PyLadiesCon Stats: Sponsors", fillable=False)

with ui.layout_columns(col_widths=[6, 2, 2, 2], height=300):
    with ui.card():
        "Campaign Funding Progress"

        @render.plot
        def plot_goal():
            return (
                ggplot(
                    funding_goal,
                    aes(x=1, y="amount", fill="segment"),
                )
                + geom_col(stat="identity", position="stack")
                + scale_fill_manual(
                    breaks=["goal", "stretch"],
                    labels=["Goal", "Stretch"],  # title case labels
                    values={"goal": "skyblue", "stretch": "gold"},
                )
                + scale_y_continuous(
                    labels=lambda l: [f"${int(v):,}" for v in l]
                )
                + labs(x="", y="")
                + coord_flip()
                + theme_tufte()
                + theme(
                    axis_ticks=element_blank(),
                    axis_text_y=element_blank(),
                    legend_background=element_rect(
                        fill="white", alpha=0.8, color="gray"
                    ),
                    # top-right corner, normalized coordinates
                    legend_position=(0.95, 0.95),
                    # align legend top-right to the position
                    legend_justification=(1, 1),
                    legend_title=element_blank(),
                )
            )

    with ui.value_box(
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-chart-column" style="color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="orange",
        class_="card-min-width",
    ):
        "Sponsorship Committed"
        f"${sponsorship_committed:,}"

    with ui.value_box(
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-sack-dollar" style="color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="success",
        class_="card-min-width",
    ):
        "Sponsorship Paid"
        f"${sponsorship_paid:,}"
        f"{sponsorship_paid_num} Sponsors"

    with ui.value_box(
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-hourglass-half" style="color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="purple",
        class_="card-min-width",
    ):
        "Pending Amount"
        f"${sponsorship_pending:,}"
        f"{sponsorship_pending_num} Sponsors"


with ui.layout_columns(col_widths=[6, 2, 2, 2], height=300):
    with ui.card():
        "Amount Paid"

        @render.plot
        def plot_paid():
            return (
                ggplot()
                + geom_col(
                    paid_funding,
                    aes(x=1, y="amount", fill="segment"),
                    stat="identity",
                    position="stack",
                )
                + geom_text(
                    pd.DataFrame({
                        "x": [1],
                        "y": [sponsorship_paid / 2],
                        "label": [f"{sponsorship_paid_pct:.0f}% Paid"],
                    }),
                    aes(x="x", y="y", label="label"),
                    color="white",
                    size=10,
                    ha="center",
                    va="center",
                    fontweight="bold",
                )
                + scale_fill_manual(
                    values={"paid": "green", "total": "lightgrey"},
                )
                + scale_y_continuous(
                    labels=lambda l: [f"${int(v):,}" for v in l]
                )
                + labs(x="", y="")
                + coord_flip()
                + theme_tufte()
                + theme(
                    axis_ticks=element_blank(),
                    axis_text_y=element_blank(),
                    legend_position="none",
                )
            )

    with ui.value_box(
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-handshake" style="color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="info",
        class_="card-min-width",
    ):
        "Sponsors Committed"
        f"{num_sponsors_committed}"
        f"{num_sponsors_contacted} contacted"

    with ui.value_box(
        showcase=ui.HTML("""
            <div style="display: flex; align-items: center; justify-content: center;
                        height: 100%; padding: 10px;">
                <i class="fas fa-bullseye" style="color: rgba(255,255,255,0.9);"></i>
            </div>
        """),
        theme="yellow",
        class_="card-min-width",
    ):
        "Percent Raised"
        f"{goal_pct:.0%}"
        f"${goal:,} Goal"

with ui.layout_columns(col_widths=[6, 6], height=300):
    with ui.card():
        "Sponsors by Status"

        @render.plot
        def plot_sponsor_status():
            return (
                ggplot(
                    sponsor_status,
                    aes(x="reorder(status, count)", y="count", fill="status"),
                )
                + geom_bar(stat="identity")
                + geom_text(
                    aes(
                        label=sponsor_status.apply(
                            lambda r: f"{r['count']} ({r['percent']:.0f}%)",
                            axis=1,
                        )
                    ),
                    ha="left",
                    nudge_y=0.5,  # move text slightly right of the bar
                    size=9,
                )
                + scale_y_continuous(
                    expand=(0, 0),
                    limits=(0, sponsor_status["count"].max() + 7),
                    breaks=lambda x: np.arange(
                        0, sponsor_status["count"].max() + 1, 10
                    ),
                )
                + labs(x="", y="")
                + coord_flip()
                + theme_tufte()
                + theme(
                    legend_position="none",
                    axis_text_y=element_text(
                        va="center",
                        ha="right",
                        linespacing=1.5,
                    ),
                )
            )

    with ui.card():
        "Sponsors by Tier"

        @render.plot
        def plot_sponsor_tier():
            return (
                ggplot(
                    sponsor_tier,
                    aes(x="reorder(tier, count)", y="count", fill="tier"),
                )
                + geom_bar(stat="identity")
                + geom_text(
                    aes(
                        label=sponsor_tier.apply(
                            lambda r: f"{r['count']} ({r['percent']:.0f}%)",
                            axis=1,
                        )
                    ),
                    ha="left",
                    nudge_y=0.1,  # move text slightly right of the bar
                    size=9,
                )
                + scale_y_continuous(
                    expand=(0, 0),
                    limits=(0, sponsor_tier["count"].max() + 2),
                    breaks=lambda x: np.arange(
                        0, sponsor_tier["count"].max() + 1, 1
                    ),
                )
                + labs(x="", y="")
                + coord_flip()
                + theme_tufte()
                + theme(
                    legend_position="none",
                )
            )
