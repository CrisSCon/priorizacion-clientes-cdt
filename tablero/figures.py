"""Prediction charts."""

from typing import Any, Sequence

import numpy as np
import plotly.graph_objects as go

GREEN = "#19715b"
RED = "#bd5853"


def probability_distribution(rows: Sequence[dict[str, Any]]) -> go.Figure:
    """Plot valid predictions in 10% bands with a 50% cutoff."""
    probabilities = [
        row["probability_yes"] for row in rows if row["probability_yes"] is not None
    ]
    counts, _ = np.histogram(probabilities, bins=np.linspace(0, 1, 11))
    figure = go.Figure(
        go.Bar(
            x=np.arange(5, 100, 10),
            y=counts.tolist(),
            width=8,
            marker_color=[RED] * 5 + [GREEN] * 5,
            customdata=[f"{n}–{n + 10}%" for n in range(0, 100, 10)],
            hovertemplate="%{customdata} probability<br>%{y} customers<extra></extra>",
        )
    )
    figure.add_vline(
        x=50,
        line_dash="dot",
        line_color="#103e38",
        annotation_text="50% cutoff",
        annotation_position="top right",
    )
    figure.update_layout(
        template="plotly_white",
        height=250,
        margin={"l": 45, "r": 20, "t": 30, "b": 45},
        font={"family": "Arial, sans-serif", "color": "#50665f", "size": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={
            "range": [0, 100],
            "ticksuffix": "%",
            "dtick": 10,
            "title": "Estimated subscription probability",
            "showgrid": False,
        },
        yaxis={
            "title": "Customers",
            "rangemode": "tozero",
            "dtick": 1 if max(counts, default=0) < 6 else None,
            "gridcolor": "#edf0ed",
        },
        showlegend=False,
    )
    if not probabilities:
        figure.add_annotation(
            text="No valid predictions to display",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    return figure
