from datetime import date
from pathlib import Path
import sqlite3

import pandas as pd

from database import DATABASE_PATH, initialize_database


def ensure_database(database_path: Path = DATABASE_PATH) -> None:
    """Create the database automatically when it does not exist."""
    if not database_path.exists():
        initialize_database(database_path=database_path)


def build_sales_filter(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    locations: list[str] | None = None,
    categories: list[str] | None = None,
) -> tuple[str, list]:
    """Build a safe parameterized SQL WHERE clause."""
    conditions = []
    parameters = []

    if start_date:
        conditions.append("date(timestamp) >= date(?)")
        parameters.append(str(start_date))

    if end_date:
        conditions.append("date(timestamp) <= date(?)")
        parameters.append(str(end_date))

    if locations:
        placeholders = ", ".join("?" for _ in locations)
        conditions.append(f"location IN ({placeholders})")
        parameters.extend(locations)

    if categories:
        placeholders = ", ".join("?" for _ in categories)
        conditions.append(f"category IN ({placeholders})")
        parameters.extend(categories)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where_clause, parameters


def get_filter_options(
    database_path: Path = DATABASE_PATH,
) -> dict:
    """Return date, location, and category choices for dashboard filters."""
    ensure_database(database_path)

    with sqlite3.connect(database_path) as connection:
        date_row = connection.execute(
            """
            SELECT
                MIN(date(timestamp)),
                MAX(date(timestamp))
            FROM sales
            """
        ).fetchone()

        locations = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT location FROM sales ORDER BY location"
            ).fetchall()
        ]

        categories = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT category FROM sales ORDER BY category"
            ).fetchall()
        ]

    return {
        "minimum_date": pd.to_datetime(date_row[0]).date(),
        "maximum_date": pd.to_datetime(date_row[1]).date(),
        "locations": locations,
        "categories": categories,
    }


def get_kpis(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    locations: list[str] | None = None,
    categories: list[str] | None = None,
    database_path: Path = DATABASE_PATH,
) -> dict:
    """Calculate the main sales and profitability metrics."""
    ensure_database(database_path)

    where_clause, parameters = build_sales_filter(
        start_date,
        end_date,
        locations,
        categories,
    )

    query = f"""
        SELECT
            COALESCE(SUM(quantity * unit_price), 0) AS revenue,
            COALESCE(SUM(quantity * unit_cost), 0) AS cost,
            COUNT(DISTINCT order_id) AS orders,
            COALESCE(SUM(quantity), 0) AS items_sold
        FROM sales
        {where_clause}
    """

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(query, parameters).fetchone()

    revenue = float(row[0])
    cost = float(row[1])
    orders = int(row[2])
    items_sold = int(row[3])
    gross_profit = revenue - cost

    return {
        "revenue": round(revenue, 2),
        "gross_profit": round(gross_profit, 2),
        "orders": orders,
        "items_sold": items_sold,
        "average_order_value": round(revenue / orders, 2) if orders else 0.0,
        "gross_margin_percent": (
            round((gross_profit / revenue) * 100, 1) if revenue else 0.0
        ),
    }


def get_daily_sales(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    locations: list[str] | None = None,
    categories: list[str] | None = None,
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Return daily revenue, profit, and order totals."""
    ensure_database(database_path)

    where_clause, parameters = build_sales_filter(
        start_date,
        end_date,
        locations,
        categories,
    )

    query = f"""
        SELECT
            date(timestamp) AS sale_date,
            ROUND(SUM(quantity * unit_price), 2) AS revenue,
            ROUND(
                SUM(quantity * (unit_price - unit_cost)),
                2
            ) AS gross_profit,
            COUNT(DISTINCT order_id) AS orders
        FROM sales
        {where_clause}
        GROUP BY date(timestamp)
        ORDER BY sale_date
    """

    with sqlite3.connect(database_path) as connection:
        result = pd.read_sql_query(query, connection, params=parameters)

    result["sale_date"] = pd.to_datetime(result["sale_date"])
    return result


def get_product_performance(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    locations: list[str] | None = None,
    categories: list[str] | None = None,
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Return product-level sales and profitability."""
    ensure_database(database_path)

    where_clause, parameters = build_sales_filter(
        start_date,
        end_date,
        locations,
        categories,
    )

    query = f"""
        SELECT
            product,
            category,
            SUM(quantity) AS quantity_sold,
            ROUND(SUM(quantity * unit_price), 2) AS revenue,
            ROUND(
                SUM(quantity * (unit_price - unit_cost)),
                2
            ) AS gross_profit
        FROM sales
        {where_clause}
        GROUP BY product, category
        ORDER BY revenue DESC
    """

    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(query, connection, params=parameters)


def get_hourly_sales(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    locations: list[str] | None = None,
    categories: list[str] | None = None,
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Return revenue and order counts by hour."""
    ensure_database(database_path)

    where_clause, parameters = build_sales_filter(
        start_date,
        end_date,
        locations,
        categories,
    )

    query = f"""
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
            ROUND(SUM(quantity * unit_price), 2) AS revenue,
            COUNT(DISTINCT order_id) AS orders
        FROM sales
        {where_clause}
        GROUP BY hour
        ORDER BY hour
    """

    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(query, connection, params=parameters)


def get_location_performance(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    locations: list[str] | None = None,
    categories: list[str] | None = None,
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Compare revenue, profit, and orders between locations."""
    ensure_database(database_path)

    where_clause, parameters = build_sales_filter(
        start_date,
        end_date,
        locations,
        categories,
    )

    query = f"""
        SELECT
            location,
            ROUND(SUM(quantity * unit_price), 2) AS revenue,
            ROUND(
                SUM(quantity * (unit_price - unit_cost)),
                2
            ) AS gross_profit,
            COUNT(DISTINCT order_id) AS orders
        FROM sales
        {where_clause}
        GROUP BY location
        ORDER BY revenue DESC
    """

    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(query, connection, params=parameters)


def get_inventory_status(
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Return inventory values and reorder warnings."""
    ensure_database(database_path)

    query = """
        SELECT
            ingredient,
            category,
            current_stock,
            reorder_level,
            unit,
            unit_cost,
            ROUND(current_stock * unit_cost, 2) AS inventory_value,
            ROUND(reorder_level - current_stock, 2) AS reorder_quantity,
            CASE
                WHEN current_stock <= reorder_level THEN 'Reorder'
                ELSE 'In Stock'
            END AS stock_status
        FROM inventory
        ORDER BY
            CASE
                WHEN current_stock <= reorder_level THEN 0
                ELSE 1
            END,
            ingredient
    """

    with sqlite3.connect(database_path) as connection:
        return pd.read_sql_query(query, connection)