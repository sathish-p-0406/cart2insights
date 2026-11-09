import pandas as pd
import plotly.express as px
import streamlit as st

import queries as q
from database import get_options, run_query
from utils import PALETTE, bar, brl, num, style

st.set_page_config(page_title="Cart2Insights", page_icon="🛒", layout="wide")
st.title("🛒 Cart2Insights: E-Commerce Performance Dashboard")

# ---------------- Sidebar filters ----------------
states_all, months_all = get_options()
st.sidebar.header("Filters")
states = st.sidebar.multiselect("Customer state", states_all, default=states_all)
default_start = "2017-01" if "2017-01" in months_all else months_all[0]
default_end = "2018-08" if "2018-08" in months_all else months_all[-1]
start, end = st.sidebar.select_slider("Period", options=months_all, value=(default_start, default_end))
st.sidebar.caption("Canceled and unavailable orders are excluded from all figures.")

if not states:
    st.warning("Select at least one state in the sidebar.")
    st.stop()


def get(sql):
    return run_query(sql, tuple(states), start, end)


tabs = st.tabs(["Business Overview", "Sales", "Customers", "Sellers & Products",
                "Delivery", "Customer Experience"])

# ---------------- 1. Business overview ----------------
with tabs[0]:
    k = get(q.KPI).iloc[0]
    sellers = get(q.SELLER_COUNT).iloc[0]["sellers"]
    c = st.columns(6)
    c[0].metric("Total revenue", brl(k["revenue"]))
    c[1].metric("Total orders", num(k["orders"]))
    c[2].metric("Total customers", num(k["customers"]))
    c[3].metric("Total sellers", num(sellers))
    c[4].metric("Avg order value", f"R$ {k['avg_order_value']:,.2f}")
    c[5].metric("Avg review score", f"{k['avg_review']:.2f} / 5")

    monthly = get(q.MONTHLY_REVENUE)
    fig = px.area(monthly, x="month", y="revenue", title="Monthly revenue", color_discrete_sequence=PALETTE)
    st.plotly_chart(style(fig), use_container_width=True)

# ---------------- 2. Sales ----------------
with tabs[1]:
    st.subheader("Sales analysis")
    monthly = get(q.MONTHLY_REVENUE)
    fig = px.line(monthly, x="month", y="revenue", markers=True, title="Monthly revenue trend",
                  color_discrete_sequence=PALETTE)
    st.plotly_chart(style(fig), use_container_width=True)

    left, right = st.columns(2)
    cat = get(q.REVENUE_BY_CATEGORY)
    left.plotly_chart(bar(cat, "revenue", "category", "Revenue by category (top 15)", horizontal=True),
                      use_container_width=True)
    state = get(q.SALES_BY_STATE).head(10)
    right.plotly_chart(bar(state, "revenue", "state", "Sales by state (top 10)", horizontal=True),
                       use_container_width=True)

    st.markdown("**Top-selling products (by units)**")
    prod = get(q.TOP_PRODUCTS)
    prod["product_id"] = prod["product_id"].str[:10] + "..."
    st.dataframe(prod, use_container_width=True, hide_index=True)

# ---------------- 3. Customers ----------------
with tabs[2]:
    st.subheader("Customer analysis")
    cust = get(q.CUSTOMER_TOTALS)
    cust["type"] = cust["orders"].apply(lambda n: "Repeat" if n > 1 else "New (one order)")

    left, right = st.columns(2)
    by_state = get(q.CUSTOMERS_BY_STATE).head(10)
    left.plotly_chart(bar(by_state, "customers", "state", "Customer distribution (top 10 states)",
                          horizontal=True), use_container_width=True)
    split = cust["type"].value_counts().reset_index()
    split.columns = ["type", "customers"]
    right.plotly_chart(style(px.pie(split, names="type", values="customers", hole=0.45,
                                    title="Repeat vs new customers",
                                    color_discrete_sequence=PALETTE)), use_container_width=True)

    cap = cust["total_spent"].quantile(0.99)
    fig = px.histogram(cust[cust["total_spent"] <= cap], x="total_spent", nbins=50,
                       title="Customer spending (up to 99th percentile)", color_discrete_sequence=PALETTE)
    st.plotly_chart(style(fig), use_container_width=True)

    st.markdown("**Top 10 customers by spending**")
    top = cust.sort_values("total_spent", ascending=False).head(10).copy()
    top["customer_unique_id"] = top["customer_unique_id"].str[:10] + "..."
    st.dataframe(top[["customer_unique_id", "orders", "total_spent"]], use_container_width=True, hide_index=True)

    repeat_pct = (cust["type"] == "Repeat").mean() * 100
    st.info(f"**Observation:** only {repeat_pct:.1f}% of customers in this selection ordered more than once. "
            "**Interpretation:** the platform is good at acquiring customers but weak at retaining them. "
            "**Business impact:** retention campaigns (coupons, follow-up emails) could grow revenue "
            "without paying for new customers.")

# ---------------- 4. Sellers & products ----------------
with tabs[3]:
    st.subheader("Seller and product analysis")
    sel = get(q.SELLER_PERFORMANCE)
    sel["seller"] = sel["seller_id"].str[:8] + "..."

    left, right = st.columns(2)
    left.plotly_chart(bar(sel, "revenue", "seller", "Top 10 sellers by revenue", horizontal=True),
                      use_container_width=True)
    right.plotly_chart(bar(sel, "seller", "avg_review", "Average rating of the top 10 sellers"),
                       use_container_width=True)
    st.dataframe(sel[["seller", "revenue", "orders", "avg_review"]], use_container_width=True, hide_index=True)

    cat = get(q.REVENUE_BY_CATEGORY)
    st.plotly_chart(bar(cat, "category", "items_sold", "Category performance: items sold"),
                    use_container_width=True)

# ---------------- 5. Delivery ----------------
with tabs[4]:
    st.subheader("Delivery analysis")
    avg_days = get(q.AVG_DELIVERY).iloc[0]["avg_delivery_days"]
    status = get(q.DELIVERY_STATUS)
    delayed_share = status.loc[status["status"] == "delayed", "orders"].sum() / max(status["orders"].sum(), 1) * 100

    c = st.columns(2)
    c[0].metric("Average delivery time", f"{avg_days} days")
    c[1].metric("Share of delayed orders", f"{delayed_share:.1f}%")

    left, right = st.columns(2)
    left.plotly_chart(style(px.pie(status, names="status", values="orders", hole=0.45,
                                   title="On-time vs delayed orders", color_discrete_sequence=PALETTE)),
                      use_container_width=True)
    right.plotly_chart(bar(status, "status", "avg_review", "Delivery status vs average review score"),
                       use_container_width=True)

    by_state = get(q.DELIVERY_BY_STATE)
    st.plotly_chart(bar(by_state, "state", "avg_delivery_days", "Average delivery days by state"),
                    use_container_width=True)

    st.info("**Observation:** delayed orders score about 2.55 on average vs 4.30 for on-time orders, and orders "
            "that never arrive score 1.74. **Interpretation:** delivery experience strongly shapes satisfaction "
            "(Welch t-test, p < 0.05). **Business impact:** improving logistics in slow states and setting "
            "realistic delivery estimates is the most direct way to lift ratings.")

# ---------------- 6. Customer experience ----------------
with tabs[5]:
    st.subheader("Customer experience")
    left, right = st.columns(2)
    dist = get(q.REVIEW_DISTRIBUTION)
    left.plotly_chart(bar(dist, "review_score", "reviews", "Review score distribution"),
                      use_container_width=True)
    by_time = get(q.REVIEW_BY_DELIVERY_TIME)
    right.plotly_chart(bar(by_time, "delivery_time", "avg_review", "Rating vs delivery performance"),
                       use_container_width=True)

    cat = get(q.REVIEWS_BY_CATEGORY)
    st.plotly_chart(bar(cat, "avg_review", "category", "Lowest-rated categories (at least 100 items)",
                        horizontal=True), use_container_width=True)
