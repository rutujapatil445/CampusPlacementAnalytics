"""
UI Styling Helper Module

Injects custom CSS styles into Streamlit for a modern, executive dashboard aesthetic.
Palettes: Indigo (#4F46E5), Teal (#0D9488), Slate (#1E293B), Crisp Metric Cards.
"""

import streamlit as st


def inject_custom_css():
    """Injects custom CSS rules for metric cards, sidebar headers, and badges."""
    st.markdown(
        """
        <style>
        /* Main Container Styling */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 95%;
        }

        /* Metric Card Container */
        .kpi-card {
            background-color: #ffffff;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        .kpi-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
        }

        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 0.2rem;
        }

        .kpi-subtitle {
            font-size: 0.78rem;
            color: #475569;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 9999px;
            text-align: center;
        }

        .badge-success {
            background-color: #DCFCE7;
            color: #166534;
        }

        .badge-warning {
            background-color: #FEF3C7;
            color: #92400E;
        }

        .badge-danger {
            background-color: #FEE2E2;
            color: #991B1B;
        }

        .badge-info {
            background-color: #E0E7FF;
            color: #3730A3;
        }

        /* Section Subheaders */
        .section-header {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1E293B;
            margin-top: 1rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 0.4rem;
        }

        /* Sidebar Branding */
        .sidebar-brand {
            font-size: 1.2rem;
            font-weight: 800;
            color: #4F46E5;
            text-align: center;
            padding: 0.8rem;
            background: #F1F5F9;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
