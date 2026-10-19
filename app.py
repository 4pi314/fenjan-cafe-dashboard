from datetime import date

import plotly.express as px
import streamlit as st

from analytics import (
    get_daily_sales,
    get_filter_options,
    get_hourly_sales,
    get_inventory_status,
    get_kpis,
    get_location_performance,
    get_product_performance,
)


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Fenjan Café Operations Dashboard",
    page_icon="☕",
    layout="wide",
)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Trebuchet MS", sans-serif;
            color: #3d2a22;
        }

        h1, h2, h3 {
            font-family: Georgia, "Times New Roman", serif;
            letter-spacing: -0.02em;
            color: #4a2c2a !important;
        }

        .dashboard-header h1 {
            font-family: Georgia, "Times New Roman", serif;
            color: white !important;
            font-weight: 700;
        }

        [data-testid="stMetricValue"] {
            color: #3d2a22;
            font-weight: 700;
        }

        [data-testid="stMetricLabel"] {
            color: #6b4a3a;
            font-weight: 600;
        }
        .stApp {
            background-color: #f8f4ee;
        }

        [data-testid="stSidebar"] {
            background-color: #ede1d2;
        }

        .dashboard-header {
            background: linear-gradient(135deg, #4a2c2a, #8b5e3c);
            color: white;
            padding: 1.6rem 2rem;
            border-radius: 16px;
            margin-bottom: 1.3rem;
        }

        .dashboard-header h1 {
            margin: 0;
            font-size: 2.2rem;
        }

        .dashboard-header p {
            margin: 0.4rem 0 0;
            color: #f4dfc8;
        }

        [data-testid="stMetric"] {
            background-color: white;
            border: 1px solid #e4d4c3;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(74, 44, 42, 0.08);
        }

        [data-testid="stMetricLabel"] {
            color: #6b4a3a;
        }

        h1, h2, h3 {
            color: #4a2c2a;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="dashboard-header">
        <h1>☕ Fenjan Café Operations Dashboard</h1>
        <p>Sales, profitability, product performance, and inventory insights</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------

filter_options = get_filter_options()

st.sidebar.header("Dashboard Filters")

selected_dates = st.sidebar.date_input(
    "Date range",
    value=(
        filter_options["minimum_date"],
        filter_options["maximum_date"],
    ),
    min_value=filter_options["minimum_date"],
    max_value=filter_options["maximum_date"],
)

selected_locations = st.sidebar.multiselect(
    "Locations",
    options=filter_options["locations"],
    default=filter_options["locations"],
)

selected_categories = st.sidebar.multiselect(
    "Product categories",
    options=filter_options["categories"],
    default=filter_options["categories"],
)

if isinstance(selected_dates, tuple):
    date_values = list(selected_dates)
else:
    date_values = [selected_dates]

if date_values:
    start_date = date_values[0]
    end_date = date_values[-1]
else:
    start_date = filter_options["minimum_date"]
    end_date = filter_options["maximum_date"]

st.sidebar.divider()
st.sidebar.caption("Portfolio project using synthetic café data.")


# ---------------------------------------------------------
# Load filtered analytics
# ---------------------------------------------------------

filters = {
    "start_date": start_date,
    "end_date": end_date,
    "locations": selected_locations,
    "categories": selected_categories,
}

kpis = get_kpis(**filters)
daily_sales = get_daily_sales(**filters)
product_performance = get_product_performance(**filters)
hourly_sales = get_hourly_sales(**filters)
location_performance = get_location_performance(**filters)
inventory = get_inventory_status()


# ---------------------------------------------------------
# KPI cards
# ---------------------------------------------------------

st.subheader("Business Overview")

kpi_columns = st.columns(5)

kpi_columns[0].metric(
    "Revenue",
    f"${kpis['revenue']:,.2f}",
)

kpi_columns[1].metric(
    "Gross Profit",
    f"${kpis['gross_profit']:,.2f}",
)

kpi_columns[2].metric(
    "Orders",
    f"{kpis['orders']:,}",
)

kpi_columns[3].metric(
    "Average Order Value",
    f"${kpis['average_order_value']:,.2f}",
)

kpi_columns[4].metric(
    "Gross Margin",
    f"{kpis['gross_margin_percent']:.1f}%",
)


# ---------------------------------------------------------
# Empty-result handling
# ---------------------------------------------------------

if daily_sales.empty:
    st.warning(
        "No sales were found for the selected filters. "
        "Try selecting more locations or categories."
    )
    st.stop()


# ---------------------------------------------------------
# Dashboard tabs
# ---------------------------------------------------------

overview_tab, products_tab, inventory_tab = st.tabs(
    [
        "📈 Sales Overview",
        "🏆 Product Performance",
        "📦 Inventory",
    ]
)


with overview_tab:
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Daily Revenue and Gross Profit")

        daily_chart_data = daily_sales.melt(
            id_vars="sale_date",
            value_vars=["revenue", "gross_profit"],
            var_name="metric",
            value_name="amount",
        )

        daily_chart = px.line(
            daily_chart_data,
            x="sale_date",
            y="amount",
            color="metric",
            markers=True,
            color_discrete_map={
                "revenue": "#8b5e3c",
                "gross_profit": "#c58b57",
            },
            labels={
                "sale_date": "Date",
                "amount": "Amount ($)",
                "metric": "Metric",
            },
        )

        daily_chart.update_layout(
            legend_title_text="",
            hovermode="x unified",
        )

        st.plotly_chart(daily_chart, use_container_width=True)

    with right_column:
        st.subheader("Revenue by Hour")

        hourly_chart = px.bar(
            hourly_sales,
            x="hour",
            y="revenue",
            color="revenue",
            color_continuous_scale=[
                "#e9d5c0",
                "#8b5e3c",
                "#4a2c2a",
            ],
            labels={
                "hour": "Hour of Day",
                "revenue": "Revenue ($)",
            },
        )

        hourly_chart.update_layout(
            coloraxis_showscale=False,
        )

        st.plotly_chart(hourly_chart, use_container_width=True)

    st.subheader("Location Performance")

    location_chart = px.bar(
        location_performance,
        x="location",
        y=["revenue", "gross_profit"],
        barmode="group",
        color_discrete_map={
            "revenue": "#8b5e3c",
            "gross_profit": "#d4a373",
        },
        labels={
            "location": "Location",
            "value": "Amount ($)",
            "variable": "Metric",
        },
    )

    location_chart.update_layout(legend_title_text="")
    st.plotly_chart(location_chart, use_container_width=True)


with products_tab:
    st.subheader("Top Products by Revenue")

    product_chart = px.bar(
        product_performance.sort_values(
            "revenue",
            ascending=True,
        ),
        x="revenue",
        y="product",
        orientation="h",
        color="category",
        labels={
            "revenue": "Revenue ($)",
            "product": "Product",
            "category": "Category",
        },
    )

    st.plotly_chart(product_chart, use_container_width=True)

    st.subheader("Product Details")

    st.dataframe(
        product_performance,
        use_container_width=True,
        hide_index=True,
        column_config={
            "product": "Product",
            "category": "Category",
            "quantity_sold": st.column_config.NumberColumn(
                "Quantity Sold",
                format="%d",
            ),
            "revenue": st.column_config.NumberColumn(
                "Revenue",
                format="$%.2f",
            ),
            "gross_profit": st.column_config.NumberColumn(
                "Gross Profit",
                format="$%.2f",
            ),
        },
    )


with inventory_tab:
    st.subheader("Inventory Status")

    reorder_inventory = inventory[
        inventory["stock_status"] == "Reorder"
    ]

    if not reorder_inventory.empty:
        st.warning(
            f"{len(reorder_inventory)} ingredients have reached "
            "their reorder level."
        )

        alert_columns = st.columns(len(reorder_inventory))

        for column, (_, item) in zip(
            alert_columns,
            reorder_inventory.iterrows(),
        ):
            column.metric(
                item["ingredient"],
                f"{item['current_stock']:g} {item['unit']}",
                delta=f"Reorder {item['reorder_quantity']:g}",
                delta_color="inverse",
            )
    else:
        st.success("All ingredients currently have sufficient stock.")

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ingredient": "Ingredient",
            "category": "Category",
            "current_stock": "Current Stock",
            "reorder_level": "Reorder Level",
            "unit": "Unit",
            "unit_cost": st.column_config.NumberColumn(
                "Unit Cost",
                format="$%.2f",
            ),
            "inventory_value": st.column_config.NumberColumn(
                "Inventory Value",
                format="$%.2f",
            ),
            "reorder_quantity": "Reorder Quantity",
            "stock_status": "Status",
        },
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()
st.caption(
    "Fenjan Café Operations Dashboard · "
    "Built with Python, SQL, Pandas, Plotly, and Streamlit"
)