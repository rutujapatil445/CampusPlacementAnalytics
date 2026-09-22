"""
Reusable UI Components Module

Provides custom rendered Streamlit widgets:
1. Header banners
2. Executive KPI Scorecards
3. Status Badges
4. Interactive Plotly Charts (Bar, Donut, Line)
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def render_header(title: str, subtitle: str = None):
    """Renders a clean section header banner."""
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"*{subtitle}*")
    st.write("---")


def render_kpi_card(title: str, value: str, subtitle: str = None, icon: str = "📊"):
    """Renders an executive KPI metric card."""
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_badge(text: str, badge_type: str = "info") -> str:
    """Returns HTML for a status badge ('success', 'warning', 'danger', 'info')."""
    valid_types = ["success", "warning", "danger", "info"]
    b_type = badge_type if badge_type in valid_types else "info"
    return f'<span class="badge badge-{b_type}">{text}</span>'


def render_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    color_col: str = None,
    barmode: str = "group",
    height: int = 400
):
    """Renders an interactive Plotly Bar Chart."""
    if df.empty:
        st.info(f"No data available for {title}.")
        return

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        barmode=barmode,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_donut_chart(
    df: pd.DataFrame,
    names_col: str,
    values_col: str,
    title: str,
    height: int = 400
):
    """Renders an interactive Plotly Donut Chart."""
    if df.empty:
        st.info(f"No data available for {title}.")
        return

    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=title,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)
