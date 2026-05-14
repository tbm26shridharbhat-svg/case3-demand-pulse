"""Outputs required by the docs (exec_summary, deck, AUDIT) must be present and non-empty."""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def test_cells_csv_present():
    p = OUT / "cells.csv"
    assert p.exists(), "outputs/cells.csv missing — re-run NB02."
    df = pd.read_csv(p)
    assert len(df) == 336


def test_forecast_csv_present():
    p = OUT / "forecast.csv"
    assert p.exists(), "outputs/forecast.csv missing — re-run NB04."
    df = pd.read_csv(p)
    assert len(df) == 7


def test_psm_results_present():
    p = OUT / "psm_results.csv"
    assert p.exists(), "outputs/psm_results.csv missing — re-run NB06."
    df = pd.read_csv(p)
    assert "hour_exact_psm" in df.estimator.values


def test_per_city_mape_present():
    p = OUT / "per_city_mape.csv"
    assert p.exists(), "outputs/per_city_mape.csv missing — re-run NB04 §7."
    df = pd.read_csv(p)
    assert len(df) == 7


def test_ab_power_present():
    p = OUT / "ab_power_analysis.csv"
    assert p.exists(), "outputs/ab_power_analysis.csv missing — re-run NB07."


def test_audit_truth_present():
    assert (ROOT / "audit_truth.json").exists(), \
        "audit_truth.json missing. Run: python scripts/canonical_audit.py --write"
