"""Data-quality contract on the supplied orders dataset.

These tests assert the shape we built every analysis on top of. If they ever fail,
the analysis numbers in the deck and exec summary cannot be trusted — fix the data
(or update the tests + audit_truth.json with intent).
"""
import pandas as pd
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "orders.csv"


@pytest.fixture(scope="module")
def orders():
    return pd.read_csv(DATA, parse_dates=["timestamp"])


def test_rows(orders):
    assert len(orders) == 50_000, "Brief documents 50k rows; data shape changed."


def test_date_range(orders):
    assert orders.timestamp.min().date().isoformat() == "2025-01-01"
    assert orders.timestamp.max().date().isoformat() == "2025-03-31"


def test_cities(orders):
    expected = {"Bangalore", "Chennai", "Delhi", "Hyderabad", "Kolkata", "Mumbai", "Pune"}
    assert set(orders.city.unique()) == expected


def test_cuisines(orders):
    expected = {"Beverages", "Biryani", "Chinese", "Continental", "Desserts",
                "Fast Food", "Italian", "North Indian", "South Indian"}
    assert set(orders.cuisine.unique()) == expected


def test_restaurants(orders):
    assert orders.restaurant_id.nunique() == 800


def test_no_nulls(orders):
    assert orders.isna().sum().sum() == 0, "Brief documents zero nulls."


def test_no_dup_order_ids(orders):
    assert orders.order_id.duplicated().sum() == 0


def test_surge_rate_within_tolerance(orders):
    # Brief documents 23.9%; we recompute to ~23.87%. Tolerance ±0.5pp.
    rate = orders.surge_applied.mean()
    assert 0.234 <= rate <= 0.244, f"surge rate drifted: {rate:.4f}"


def test_columns_unchanged(orders):
    expected = ["order_id", "timestamp", "city", "restaurant_id", "cuisine",
                "order_value", "delivery_time_min", "surge_applied"]
    assert list(orders.columns) == expected
