"""Canonical truth table — recompute every number quoted in the submission.

Run from project root:
    source .venv/bin/activate
    python scripts/canonical_audit.py

Any document or notebook that quotes a different number than this script produces is wrong.
See AUDIT.md for the cross-reference matrix.
"""
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from sklearn.metrics import silhouette_score
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(42)
df = pd.read_csv(ROOT / "data" / "orders.csv", parse_dates=["timestamp"])
df["hour"] = df.timestamp.dt.hour
df["dow_num"] = df.timestamp.dt.dayofweek
df["day_bucket"] = np.where(df.dow_num >= 5, "weekend", "weekday")
df["date"] = df.timestamp.dt.normalize()

T = {}

# Basic facts
T["rows"] = len(df)
T["surge_rate_overall_%"] = round(df.surge_applied.mean() * 100, 2)
T["aov_mean"] = round(df.order_value.mean(), 2)
T["aov_median"] = int(df.order_value.median())
T["aov_p95"] = int(df.order_value.quantile(0.95))
T["delivery_mean"] = round(df.delivery_time_min.mean(), 2)
T["delivery_p95"] = int(df.delivery_time_min.quantile(0.95))

# Hour curve
hr = df.groupby("hour").agg(n=("order_id", "size"), s=("surge_applied", "sum"))
hr["sr"] = hr.s / hr.n
for h in [12, 13, 18, 19, 20, 21, 22]:
    T[f"hour{h}_orders"] = int(hr.loc[h, "n"])
    T[f"hour{h}_surge_%"] = round(hr.loc[h, "sr"] * 100, 1)
T["pearson_r"] = round((hr.n / hr.n.sum()).corr(hr.sr), 3)

# Cells
cell = (df.groupby(["city", "day_bucket", "hour"])
          .agg(n=("order_id", "size"), s=("surge_applied", "sum")).reset_index())
cell["sr"] = cell.s / cell.n
cell["d_pct"] = cell.groupby("city").n.rank(pct=True, method="average")
cell["s_pct"] = cell.groupby("city").sr.rank(pct=True, method="average")
def cls(r):
    if r.d_pct <= 0.50 and r.s_pct >= 0.50: return "W"
    if r.d_pct >= 0.75 and r.s_pct <= 0.50: return "G"
    return "A"
cell["c"] = cell.apply(cls, axis=1)
T["cells_total"] = len(cell)
T["cells_waste"] = int((cell.c == "W").sum())
T["cells_gap"] = int((cell.c == "G").sum())
T["cells_aligned"] = int((cell.c == "A").sum())
W = cell[cell.c == "W"]
T["total_surge_events"] = int(cell.s.sum())
T["waste_surge_orders"] = int(W.s.sum())
T["waste_spend_90d_inr"] = int(W.s.sum() * 20)
T["waste_spend_mo_inr"] = int(W.s.sum() * 20 * 30 / 90)
T["waste_share_%"] = round(W.s.sum() / cell.s.sum() * 100, 1)
T["above_med_demand_share_%"] = round(cell[cell.d_pct > 0.5].s.sum() / cell.s.sum() * 100, 1)
T["below_med_demand_share_%"] = round(cell[cell.d_pct <= 0.5].s.sum() / cell.s.sum() * 100, 1)

# Cohorts
shape = df.groupby(["city", "day_bucket", "hour"]).size().unstack("hour", fill_value=0)
shape_n = shape.div(shape.sum(axis=1), axis=0)
dist = pdist(shape_n.values)
T["dist_max"] = round(dist.max(), 3)
T["dist_median"] = round(np.median(dist), 3)
Z = linkage(shape_n.values, method="ward")
T["sil_k2"] = round(silhouette_score(shape_n.values, fcluster(Z, t=2, criterion="maxclust")), 3)
T["sil_k3"] = round(silhouette_score(shape_n.values, fcluster(Z, t=3, criterion="maxclust")), 3)

# Forecast — Mumbai (chosen on backtest evidence, see DECISIONS.md)
mumbai = df[df.city == "Mumbai"].groupby("date").size().rename("orders")
mumbai.index = pd.DatetimeIndex(mumbai.index, freq="D")
def mape(a, p): return float(np.mean(np.abs((np.asarray(a, float) - np.asarray(p, float)) / a)) * 100)
def naive(t): return pd.Series(t.iloc[-7:].values)
def hw(t):
    return ExponentialSmoothing(t, seasonal_periods=7, trend="add", seasonal="add").fit().forecast(7).reset_index(drop=True)
def sar(t):
    return SARIMAX(t, order=(1,1,1), seasonal_order=(1,1,1,7),
        enforce_stationarity=False, enforce_invertibility=False).fit(disp=False).forecast(7).reset_index(drop=True)
def walk(series, fn, h=7, n=3):
    rows = []
    for w in range(n):
        e = len(series) - w * h
        s = e - h
        train, test = series.iloc[:s], series.iloc[s:e]
        fc = fn(train).iloc[:h].values
        rows.append(pd.DataFrame({"a": test.values, "p": fc, "dow": test.index.dayofweek}))
    return pd.concat(rows)
for name, fn in [("naive", naive), ("hw", hw), ("sarima", sar)]:
    bt = walk(mumbai, fn)
    T[f"mumbai_mape_{name}_pooled_%"] = round(mape(bt.a, bt.p), 2)
    T[f"mumbai_mape_{name}_wd_%"] = round(mape(bt[bt.dow < 5].a, bt[bt.dow < 5].p), 2)
    T[f"mumbai_mape_{name}_we_%"] = round(mape(bt[bt.dow >= 5].a, bt[bt.dow >= 5].p), 2)

# Cuisine hour-18 lift
h18 = df[df.hour == 18].cuisine.value_counts(normalize=True) * 100
sh = df.cuisine.value_counts(normalize=True) * 100
lift = (h18 - sh).round(2)
T["hour18_lift_beverages_pp"] = round(lift["Beverages"], 1)
T["hour18_lift_north_indian_pp"] = round(lift["North Indian"], 1)

# Restaurants
r = df.restaurant_id.value_counts()
T["top10_share_%"] = round(r.head(10).sum() / len(df) * 100, 2)
T["top50_share_%"] = round(r.head(50).sum() / len(df) * 100, 2)
T["top100_share_%"] = round(r.head(100).sum() / len(df) * 100, 2)
T["restaurant_median"] = int(r.median())

# AOV
T["aov_surge1"] = round(df[df.surge_applied == 1].order_value.mean(), 0)
T["aov_surge0"] = round(df[df.surge_applied == 0].order_value.mean(), 0)

# Delivery
T["delivery_surge1"] = round(df[df.surge_applied == 1].delivery_time_min.mean(), 2)
T["delivery_surge0"] = round(df[df.surge_applied == 0].delivery_time_min.mean(), 2)
T["delivery_diff_pct_%"] = round((T["delivery_surge1"] / T["delivery_surge0"] - 1) * 100, 1)
ph = df.groupby(["hour", "surge_applied"]).delivery_time_min.mean().unstack().round(2)
ph.columns = ["ns", "s"]
ph["d"] = ph.s - ph.ns
for h in [0, 12, 13, 19, 20, 21]:
    T[f"delivery_h{h}_ns"] = round(ph.loc[h, "ns"], 2)
    T[f"delivery_h{h}_s"] = round(ph.loc[h, "s"], 2)
    T[f"delivery_h{h}_d"] = round(ph.loc[h, "d"], 2)

# City volumes
v = df.groupby("city").size().sort_values(ascending=False)
T["bangalore_vol"] = int(v["Bangalore"])
T["mumbai_vol"] = int(v["Mumbai"])
T["delhi_vol"] = int(v["Delhi"])

# Hour-exact PSM (Notebook 06)
df["weekend"] = (df.dow_num >= 5).astype(int)
df["log_value"] = np.log1p(df.order_value)
X_cat = pd.get_dummies(df[["city", "cuisine"]], drop_first=False).astype(float).values
X_cont = StandardScaler().fit_transform(df[["log_value", "weekend"]].values)
X_ps = np.hstack([X_cont, X_cat])
ps_model = LogisticRegression(max_iter=2000, C=1.0).fit(X_ps, df.surge_applied.values)
df["logit_ps"] = np.log(ps_model.predict_proba(X_ps)[:, 1] /
                        (1 - ps_model.predict_proba(X_ps)[:, 1]))
caliper = 0.2 * df.logit_ps.std()

all_deltas = []
for h in range(24):
    t = df[(df.surge_applied == 1) & (df.hour == h)]
    c = df[(df.surge_applied == 0) & (df.hour == h)]
    if len(t) < 5 or len(c) < 5:
        continue
    nn = NearestNeighbors(n_neighbors=1).fit(c[["logit_ps"]].values)
    d, idx = nn.kneighbors(t[["logit_ps"]].values)
    within = d.flatten() <= caliper
    mt = t[within].reset_index(drop=True)
    mc = c.iloc[idx.flatten()[within]].reset_index(drop=True)
    all_deltas.append(mt.delivery_time_min.values - mc.delivery_time_min.values)
flat = np.concatenate(all_deltas)
boot = np.array([flat[RNG.choice(len(flat), len(flat), replace=True)].mean()
                 for _ in range(1000)])
T["psm_hour_exact_att_min"] = round(float(flat.mean()), 3)
T["psm_hour_exact_ci_low"] = round(float(np.percentile(boot, 2.5)), 3)
T["psm_hour_exact_ci_high"] = round(float(np.percentile(boot, 97.5)), 3)
T["psm_n_pairs"] = int(len(flat))

for k, val in sorted(T.items()):
    print(f"{k:42s} = {val}")
