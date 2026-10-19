from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data")
RANDOM_SEED = 42
NUMBER_OF_ORDERS = 4_500


PRODUCTS = pd.DataFrame(
    [
        {"product": "Adeni Chai", "category": "Tea", "price": 5.50, "cost": 1.35, "weight": 0.15},
        {"product": "Qishr", "category": "Tea", "price": 5.00, "cost": 1.10, "weight": 0.08},
        {"product": "Yemeni Latte", "category": "Coffee", "price": 6.50, "cost": 1.75, "weight": 0.11},
        {"product": "Pistachio Latte", "category": "Coffee", "price": 7.00, "cost": 2.10, "weight": 0.09},
        {"product": "Cardamom Latte", "category": "Coffee", "price": 6.75, "cost": 1.90, "weight": 0.08},
        {"product": "Espresso", "category": "Coffee", "price": 3.75, "cost": 0.70, "weight": 0.08},
        {"product": "Americano", "category": "Coffee", "price": 4.50, "cost": 0.85, "weight": 0.10},
        {"product": "Cappuccino", "category": "Coffee", "price": 5.75, "cost": 1.45, "weight": 0.08},
        {"product": "Honey Cake", "category": "Dessert", "price": 7.50, "cost": 2.65, "weight": 0.10},
        {"product": "Pistachio Croissant", "category": "Pastry", "price": 6.25, "cost": 2.20, "weight": 0.07},
        {"product": "Date Cookie", "category": "Pastry", "price": 3.50, "cost": 1.05, "weight": 0.06},
    ]
)


def generate_sales() -> pd.DataFrame:
    """Create reproducible synthetic café transaction data."""
    rng = np.random.default_rng(RANDOM_SEED)

    end_date = pd.Timestamp.today().normalize()
    dates = pd.date_range(end=end_date, periods=90, freq="D")

    date_weights = np.array(
        [1.3 if date.dayofweek in (4, 5, 6) else 1.0 for date in dates]
    )
    date_weights = date_weights / date_weights.sum()

    hours = np.arange(7, 22)
    hour_weights = (
        np.exp(-((hours - 10) ** 2) / 7)
        + 0.85 * np.exp(-((hours - 17) ** 2) / 10)
        + 0.15
    )
    hour_weights = hour_weights / hour_weights.sum()

    rows = []

    for order_number in range(1, NUMBER_OF_ORDERS + 1):
        order_date = dates[rng.choice(len(dates), p=date_weights)]
        order_hour = int(rng.choice(hours, p=hour_weights))
        order_minute = int(rng.integers(0, 60))

        timestamp = order_date + pd.Timedelta(
            hours=order_hour,
            minutes=order_minute,
        )

        order_id = f"FEN-{order_number:05d}"
        location = str(rng.choice(["Downtown", "Waterfront"], p=[0.58, 0.42]))
        payment_method = str(
            rng.choice(["Card", "Mobile Wallet", "Cash"], p=[0.62, 0.25, 0.13])
        )
        item_count = int(rng.choice([1, 2, 3], p=[0.76, 0.21, 0.03]))

        chosen_products = rng.choice(
            PRODUCTS.index,
            size=item_count,
            replace=False,
            p=PRODUCTS["weight"],
        )

        for product_index in chosen_products:
            product = PRODUCTS.loc[product_index]
            quantity = int(rng.choice([1, 2, 3], p=[0.86, 0.12, 0.02]))

            rows.append(
                {
                    "order_id": order_id,
                    "timestamp": timestamp,
                    "location": location,
                    "product": product["product"],
                    "category": product["category"],
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "unit_cost": product["cost"],
                    "payment_method": payment_method,
                }
            )

    return (
        pd.DataFrame(rows)
        .sort_values(["timestamp", "order_id"])
        .reset_index(drop=True)
    )


def generate_inventory() -> pd.DataFrame:
    """Create synthetic inventory levels, including several low-stock items."""
    return pd.DataFrame(
        [
            ["Coffee Beans", "Beverage", 42.0, 20.0, "kg", 18.50],
            ["Black Tea", "Beverage", 18.0, 8.0, "kg", 13.00],
            ["Cardamom", "Spice", 5.5, 3.0, "kg", 27.00],
            ["Fresh Ginger", "Produce", 7.0, 4.0, "kg", 5.50],
            ["Whole Milk", "Dairy", 48.0, 25.0, "gallons", 4.30],
            ["Oat Milk", "Dairy", 9.0, 12.0, "cases", 23.00],
            ["Pistachio Syrup", "Flavoring", 4.0, 6.0, "bottles", 14.50],
            ["Honey", "Flavoring", 11.0, 5.0, "jars", 10.00],
            ["Pastry Dough", "Bakery", 16.0, 10.0, "cases", 31.00],
            ["Dates", "Bakery", 13.0, 6.0, "kg", 12.00],
            ["Paper Cups", "Packaging", 350.0, 500.0, "units", 0.12],
            ["Cup Lids", "Packaging", 720.0, 500.0, "units", 0.06],
        ],
        columns=[
            "ingredient",
            "category",
            "current_stock",
            "reorder_level",
            "unit",
            "unit_cost",
        ],
    )


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    sales = generate_sales()
    inventory = generate_inventory()

    sales.to_csv(DATA_DIR / "sales.csv", index=False)
    inventory.to_csv(DATA_DIR / "inventory.csv", index=False)

    print(f"Created {len(sales):,} sales line items.")
    print(f"Created {len(inventory):,} inventory records.")
    print(f"Unique orders: {sales['order_id'].nunique():,}")
    print(f"Date range: {sales['timestamp'].min()} to {sales['timestamp'].max()}")


if __name__ == "__main__":
    main()