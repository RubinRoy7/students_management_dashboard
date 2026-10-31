from collections.abc import Sequence
from typing import Any, Mapping

import plotly.graph_objects as go
import streamlit as st

PLOTLY_CATEGORICAL_COLORS = [
    "#42D9FF",
    "#9B8CFF",
    "#35D6A4",
    "#FFB86B",
    "#FF6FAE",
    "#78A9FF",
]

PLOTLY_SEQUENTIAL_SCALE = [
    [0, "#10243A"],
    [0.35, "#15516B"],
    [0.7, "#168EAA"],
    [1, "#42D9FF"],
]

PLOTLY_DIVERGING_SCALE = [
    [0, "#9B8CFF"],
    [0.5, "#10243A"],
    [1, "#42D9FF"],
]


def render_page_header(title: str, description: str) -> None:
    """Render a consistent page title and supporting description."""
    st.title(title)
    st.caption(description)


def render_metric_cards(
    metrics: Sequence[tuple[str, str | int | float, str | None]],
    columns: int = 4,
) -> None:
    """Render metrics in consistent, native Streamlit bordered cards."""
    if columns < 1:
        raise ValueError("columns must be at least 1")

    for start in range(0, len(metrics), columns):
        metric_columns = st.columns(min(columns, len(metrics) - start))
        for column, (label, value, help_text) in zip(
            metric_columns,
            metrics[start:start + columns],
        ):
            with column:
                with st.container(border=True):
                    st.metric(label, value, help=help_text)


def render_chart(figure: go.Figure, config: Mapping[str, Any]) -> None:
    """Display a Plotly figure in a native bordered Streamlit container."""
    with st.container(border=True):
        st.plotly_chart(
            figure,
            use_container_width=True,
            config=dict(config),
        )


def style_plotly_figure(figure):
    """Apply the dashboard's dark data-studio palette to Plotly figures."""
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PLOTLY_CATEGORICAL_COLORS,
        font=dict(family="Segoe UI, sans-serif", color="#DCEBFA", size=13),
        title=dict(x=0.02, xanchor="left", font=dict(size=18, color="#F1F7FF")),
        margin=dict(l=20, r=20, t=58, b=24),
        hoverlabel=dict(
            bgcolor="#101D30",
            bordercolor="#42D9FF",
            font=dict(color="#F1F7FF", size=13),
        ),
        legend=dict(
            bgcolor="rgba(16,29,48,0.72)",
            borderwidth=0,
            font=dict(color="#C6D9ED"),
        ),
    )
    figure.update_xaxes(
        showgrid=False,
        linecolor="#29425D",
        tickfont=dict(color="#A8BCD2"),
        title_font=dict(color="#C6D9ED"),
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor="rgba(133,167,201,0.14)",
        zerolinecolor="#29425D",
        tickfont=dict(color="#A8BCD2"),
        title_font=dict(color="#C6D9ED"),
    )
    return figure
