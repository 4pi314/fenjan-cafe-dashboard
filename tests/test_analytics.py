import shutil
from pathlib import Path

import pytest

from analytics import (
    build_sales_filter,
    get_daily_sales,
    get_filter_options,
    get_hourly_sales,
    get_inventory_status,
    get_kpis,
    get_location_performance,
    get_product_performance,
)


SOURCE_DATABASE = Path("data/fenjan_cafe.db")


@pytest.fixture
def test_database(tmp_path):
    """Create an isolated database copy for each test."""
    database_path = tmp_path / "fenjan_cafe_test.db"
    shutil.copy2(SOURCE_DATABASE, database_path)
    return database_path


def test_filter_options(test_database):
    options = get_filter_options(test_database)

    assert options["minimum_date"].isoformat() == "2026-07-21"
    assert options["maximum_date"].isoformat() == "2026-10-18"
    assert options["locations"] == ["Downtown", "Waterfront"]
    assert options["categories"] == ["Coffee", "Dessert", "Pastry", "Tea"]


def test_complete_kpis(test_database):
    kpis = get_kpis(database_path=test_database)

    assert kpis["revenue"] == pytest.approx(37868.50)
    assert kpis["gross_profit"] == pytest.approx(27560.55)
    assert kpis["orders"] == 4500
    assert kpis["items_sold"] == 6664
    assert kpis["average_order_value"] == pytest.approx(8.42)
    assert kpis["gross_margin_percent"] == pytest.approx(72.8)


def test_location_filter_reduces_results(test_database):
    complete = get_kpis(database_path=test_database)
    downtown = get_kpis(
        locations=["Downtown"],
        database_path=test_database,
    )

    assert 0 < downtown["revenue"] < complete["revenue"]
    assert 0 < downtown["orders"] < complete["orders"]


def test_category_filter_reduces_results(test_database):
    complete = get_kpis(database_path=test_database)
    coffee = get_kpis(
        categories=["Coffee"],
        database_path=test_database,
    )

    assert 0 < coffee["revenue"] < complete["revenue"]
    assert 0 < coffee["items_sold"] < complete["items_sold"]


def test_date_filter_reduces_results(test_database):
    complete = get_kpis(database_path=test_database)
    single_day = get_kpis(
        start_date="2026-10-18",
        end_date="2026-10-18",
        database_path=test_database,
    )

    assert 0 < single_day["orders"] < complete["orders"]
    assert 0 < single_day["revenue"] < complete["revenue"]


def test_empty_filter_lists_are_ignored():
    sql, parameters = build_sales_filter(
        locations=[],
        categories=[],
    )

    assert sql == ""
    assert parameters == []


def test_sales_analytics_return_data(test_database):
    daily = get_daily_sales(database_path=test_database)
    products = get_product_performance(database_path=test_database)
    hourly = get_hourly_sales(database_path=test_database)
    locations = get_location_performance(database_path=test_database)

    assert not daily.empty
    assert not products.empty
    assert not hourly.empty
    assert not locations.empty
    assert len(locations) == 2


def test_inventory_reorder_alerts(test_database):
    inventory = get_inventory_status(test_database)

    reorder_items = set(
        inventory.loc[
            inventory["stock_status"] == "Reorder",
            "ingredient",
        ]
    )

    assert reorder_items == {
        "Oat Milk",
        "Paper Cups",
        "Pistachio Syrup",
    }


def test_inventory_contains_twelve_ingredients(test_database):
    inventory = get_inventory_status(test_database)

    assert len(inventory) == 12
    assert set(inventory["stock_status"]) == {"In Stock", "Reorder"}
    assert (inventory["reorder_quantity"] >= 0).all()