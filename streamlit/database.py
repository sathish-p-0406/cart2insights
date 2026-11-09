import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, text

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")  # optional: only needed if you use MySQL


@st.cache_resource
def get_engine():
    """SQLite by default. For MySQL put DATABASE_URL in .env, e.g.
    DATABASE_URL=mysql+pymysql://user:password@localhost/cart2insights"""
    url = os.getenv("DATABASE_URL") or f"sqlite:///{BASE / 'cart2insights.db'}"
    return create_engine(url)


@st.cache_data(show_spinner=False)
def run_query(sql, states, start, end):
    """Run a filtered query. states is a tuple, start/end are 'YYYY-MM' strings."""
    stmt = text(sql).bindparams(bindparam("states", expanding=True))
    with get_engine().connect() as conn:
        return pd.read_sql(stmt, conn, params={"states": list(states), "start": start, "end": end})


@st.cache_data(show_spinner=False)
def get_options():
    with get_engine().connect() as conn:
        states = pd.read_sql(text(
            "SELECT DISTINCT customer_state FROM order_features "
            "WHERE customer_state IS NOT NULL ORDER BY 1"), conn)["customer_state"].tolist()
        months = pd.read_sql(text(
            "SELECT DISTINCT purchase_month FROM order_features ORDER BY 1"), conn)["purchase_month"].tolist()
    return states, months
    