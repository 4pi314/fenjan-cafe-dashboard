from pathlib import Path
import sqlite3

import pandas as pd


DATA_DIR = Path("data")
DATABASE_PATH = DATA_DIR / "fenjan_cafe.db"
SALES_CSV_PATH = DATA_DIR / "sales.csv"
INVENTORY_CSV_PATH = DATA_DIR / "inventory.csv"


DATABASE_SCHEMA = """
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS inventory;

CREATE TABLE sales (
    sale_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    location TEXT NOT NULL,
    product TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    payment_method TEXT NOT NULL
);

CREATE TABLE inventory (
    ingredient TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    current_stock REAL NOT NULL CHECK (current_stock >= 0),
    reorder_level REAL NOT NULL CHECK (reorder_level >= 0),
    unit TEXT NOT NULL,
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0)
);

CREATE INDEX index_sales_timestamp ON sales(timestamp);
CREATE INDEX index_sales_order_id ON sales(order_id);
CREATE INDEX index_sales_location ON sales(location);
CREATE INDEX index_sales_product ON sales(product);
CREATE INDEX index_sales_category ON sales(category);
"""


def load_csv_files(
    sales_path: Path = SALES_CSV_PATH,
    inventory_path: Path = INVENTORY_CSV_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate the generated CSV files."""
    if not sales_path.exists():
        raise FileNotFoundError(f"Sales file not found: {sales_path}")

    if not inventory_path.exists():
        raise FileNotFoundError(f"Inventory file not found: {inventory_path}")

    sales = pd.read_csv(sales_path)
    inventory = pd.read_csv(inventory_path)

    return sales, inventory


def initialize_database(
    database_path: Path = DATABASE_PATH,
    sales_path: Path = SALES_CSV_PATH,
    inventory_path: Path = INVENTORY_CSV_PATH,
) -> tuple[int, int]:
    """Create the SQLite database and import the CSV data."""
    sales, inventory = load_csv_files(sales_path, inventory_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.executescript(DATABASE_SCHEMA)

        sales.to_sql(
            "sales",
            connection,
            if_exists="append",
            index=False,
        )

        inventory.to_sql(
            "inventory",
            connection,
            if_exists="append",
            index=False,
        )

        sales_count = connection.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        inventory_count = connection.execute(
            "SELECT COUNT(*) FROM inventory"
        ).fetchone()[0]

    return sales_count, inventory_count


def main() -> None:
    sales_count, inventory_count = initialize_database()

    print(f"Database created: {DATABASE_PATH}")
    print(f"Sales rows imported: {sales_count:,}")
    print(f"Inventory rows imported: {inventory_count:,}")


if __name__ == "__main__":
    main()