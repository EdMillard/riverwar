"""
Lake Powell 24-Month Study inflow traces
Climatology period: water years 2000–2026 (user-supplied)
Monthly unregulated inflow is the correct resolution for 24MS.

Two methods:
  A) Official-style single traces from monthly percentiles
  B) Year-block Monte Carlo / all year-pair permutations
     -> Most Probable = median of ensemble
     -> Probable Minimum = low percentile of ensemble

USBR official Year-1 uses CBRFC ESP (current basin state + historical weather).
This code cannot recreate that snow/soil initialization. Optional: splice a
CBRFC remaining-year forecast into Year 1, then use new-period climatology after.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WATER_YEAR_MONTHS = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # Oct–Sep
MONTH_LABELS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar",
                "Apr", "May", "Jun", "Jul", "Aug", "Sep"]

# Official 24MS-style percentiles (Upper Basin)
P_MOST = 50
P_MIN_Y1 = 10   # first water year of Probable Minimum
P_MIN_Y2 = 25   # second water year of Probable Minimum
P_MAX_Y1 = 90
P_MAX_Y2 = 75


# ---------------------------------------------------------------------------
# Load / normalize data
# ---------------------------------------------------------------------------
def water_year(ts: pd.Series) -> pd.Series:
    """Water year = calendar year of the following Sep (Oct 2000 -> WY 2001)."""
    return np.where(ts.dt.month >= 10, ts.dt.year + 1, ts.dt.year)


def load_inflows(path: str | Path, value_col: str | None = None) -> pd.DataFrame:
    """
    Accepts either:
      - daily or monthly series with a date column + inflow column
      - already-monthly table with water_year, month, inflow

    Units: keep consistent (acre-feet recommended). Daily values are
    summed to monthly. Do not average daily cfs without converting to volume.
    """
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if {"water_year", "month"}.issubset(df.columns):
        val = value_col or next(
            c for c in df.columns
            if c not in {"water_year", "month", "year", "wy"}
        )
        out = df.rename(columns={val: "inflow"})[["water_year", "month", "inflow"]].copy()
        out["water_year"] = out["water_year"].astype(int)
        out["month"] = out["month"].astype(int)
        return out

    date_col = next(c for c in df.columns if "date" in c or c in {"datetime", "time"})
    val = value_col or next(c for c in df.columns if c != date_col)
    df[date_col] = pd.to_datetime(df[date_col])
    df["water_year"] = water_year(df[date_col])
    df["month"] = df[date_col].dt.month
    monthly = (
        df.groupby(["water_year", "month"], as_index=False)[val]
        .sum()
        .rename(columns={val: "inflow"})
    )
    return monthly


def wy_matrix(monthly: pd.DataFrame, wy_start: int = 2000, wy_end: int = 2026) -> pd.DataFrame:
    """
    Rows = water years, columns = Oct..Sep monthly volumes.
    Incomplete years (e.g. current WY) are kept but flagged.
    Note: WY 2000 is Oct 1999–Sep 2000. Adjust wy_start if your file is calendar years.
    """
    m = monthly[(monthly.water_year >= wy_start) & (monthly.water_year <= wy_end)].copy()
    wide = (
        m.pivot_table(index="water_year", columns="month", values="inflow", aggfunc="sum")
        .reindex(columns=WATER_YEAR_MONTHS)
    )
    wide.columns = MONTH_LABELS
    wide["annual"] = wide[MONTH_LABELS].sum(axis=1, min_count=12)
    wide["complete"] = wide[MONTH_LABELS].notna().all(axis=1)
    return wide


# ---------------------------------------------------------------------------
# A) Official-style climatology traces (single constructed traces)
# ---------------------------------------------------------------------------
def monthly_percentiles(wide: pd.DataFrame, percentiles=(10, 25, 50, 75, 90)) -> pd.DataFrame:
    complete = wide.loc[wide["complete"], MONTH_LABELS]
    rows = []
    for p in percentiles:
        rows.append(complete.quantile(p / 100.0))
    stats = pd.DataFrame(rows, index=[f"p{p:02d}" for p in percentiles])
    stats["annual"] = stats.sum(axis=1)
    return stats


def official_style_trace(
    stats: pd.DataFrame,
    n_months: int = 24,
    start_month: str = "Oct",
    scenario: str = "most",  # most | min | max
    year1_forecast: pd.Series | None = None,
) -> pd.Series:
    """
    Build one 24-month trace the way 24MS does for the *out-year*:
      most: all months at p50
      min:  Year-1 months at p10, Year-2 months at p25
      max:  Year-1 months at p90, Year-2 months at p75

    If year1_forecast is provided (index = month labels for remaining current WY),
    those values replace climatology until they run out. That is the right way
    to mix a live CBRFC forecast with a new 2000–2026 climatology.
    """
    start_i = MONTH_LABELS.index(start_month)
    months = [MONTH_LABELS[(start_i + i) % 12] for i in range(n_months)]

    def pick(i, month):
        in_year1 = i < (12 - start_i)  # remaining months of current WY, then next WY is year 2
        # Simpler operational rule used in many 24MS descriptions:
        # first 12 forecast months = Y1 percentiles, next 12 = Y2 percentiles
        in_year1 = i < 12
        if scenario == "most":
            key = "p50"
        elif scenario == "min":
            key = "p10" if in_year1 else "p25"
        elif scenario == "max":
            key = "p90" if in_year1 else "p75"
        else:
            raise ValueError(scenario)
        return float(stats.loc[key, month])

    vals = []
    for i, mon in enumerate(months):
        if year1_forecast is not None and mon in year1_forecast.index and i < len(year1_forecast):
            # only splice forecast onto the leading months you actually have
            if i < len(year1_forecast) and year1_forecast.index[i] == mon:
                vals.append(float(year1_forecast.iloc[i]))
                continue
        vals.append(pick(i, mon))

    idx = pd.period_range(start=f"2026-{start_month}", periods=n_months, freq="M")
    # Period start year is a placeholder; relabel as you like
    return pd.Series(vals, index=months, name=scenario)


# ---------------------------------------------------------------------------
# B) Monte Carlo / all permutations of historical water years
# ---------------------------------------------------------------------------
def two_year_sequence(wide: pd.DataFrame, wy_a: int, wy_b: int, start_month: str = "Oct") -> np.ndarray:
    """Concatenate two water years, then rotate so the sequence starts at start_month."""
    a = wide.loc[wy_a, MONTH_LABELS].to_numpy(dtype=float)
    b = wide.loc[wy_b, MONTH_LABELS].to_numpy(dtype=float)
    seq = np.concatenate([a, b])  # Oct_a ... Sep_a, Oct_b ... Sep_b
    if start_month != "Oct":
        # For a mid-year study start you normally keep observed months
        # and only sample the unknown future. See remaining_year_mc().
        shift = MONTH_LABELS.index(start_month)
        seq = np.concatenate([a[shift:], b, a[:shift]])[:24]
    return seq


def all_year_pair_ensemble(wide: pd.DataFrame, start_month: str = "Oct") -> pd.DataFrame:
    """
    Every ordered pair of complete water years (n^2 traces).
    Independent resampling: year 2 does not have to follow year 1 in history.
    For n=26 this is 676 traces — small enough to enumerate exactly.
    """
    years = wide.index[wide["complete"]].astype(int).tolist()
    rows = []
    labels = None
    start_i = MONTH_LABELS.index(start_month)
    month_names = [MONTH_LABELS[(start_i + i) % 12] for i in range(24)]
    yr_tag = [1] * (12 - start_i) + [2] * 12 + [3] * start_i
    col_names = [f"Y{yr_tag[i]}_{month_names[i]}" for i in range(24)]

    for ya, yb in product(years, years):
        seq = two_year_sequence(wide, ya, yb, start_month="Oct")
        if start_month != "Oct":
            seq = two_year_sequence(wide, ya, yb, start_month=start_month)
        rows.append(seq)
    ens = pd.DataFrame(rows, columns=col_names)
    ens["year1"] = [p[0] for p in product(years, years)]
    ens["year2"] = [p[1] for p in product(years, years)]
    ens["total_24mo"] = ens[col_names].sum(axis=1)
    return ens


def sequential_pair_ensemble(wide: pd.DataFrame, start_month: str = "Oct") -> pd.DataFrame:
    """
    Index-sequential pairs: (WY t, WY t+1), wrapping the record (Reclamation ISM style).
    Preserves observed year-to-year persistence. n traces instead of n^2.
    """
    years = wide.index[wide["complete"]].astype(int).tolist()
    pairs = [(years[i], years[(i + 1) % len(years)]) for i in range(len(years))]
    start_i = MONTH_LABELS.index(start_month)
    month_names = [MONTH_LABELS[(start_i + i) % 12] for i in range(24)]
    col_names = [f"m{i+1:02d}_{month_names[i]}" for i in range(24)]
    rows = [two_year_sequence(wide, a, b, start_month) for a, b in pairs]
    ens = pd.DataFrame(rows, columns=col_names)
    ens["year1"] = [a for a, _ in pairs]
    ens["year2"] = [b for _, b in pairs]
    ens["total_24mo"] = ens[col_names].sum(axis=1)
    return ens


def monte_carlo_pairs(
    wide: pd.DataFrame,
    n_sims: int = 20_000,
    seed: int = 42,
    preserve_persistence: bool = False,
    start_month: str = "Oct",
) -> pd.DataFrame:
    """
    Sample year pairs with replacement.
    preserve_persistence=True samples a start year then uses the next historical year
    (wraps), which is a block bootstrap of length 2.
    """
    rng = np.random.default_rng(seed)
    years = wide.index[wide["complete"]].astype(int).to_numpy()
    n = len(years)
    start_i = MONTH_LABELS.index(start_month)
    month_names = [MONTH_LABELS[(start_i + i) % 12] for i in range(24)]
    col_names = [f"m{i+1:02d}_{month_names[i]}" for i in range(24)]

    if preserve_persistence:
        i0 = rng.integers(0, n, size=n_sims)
        ya = years[i0]
        yb = years[(i0 + 1) % n]
    else:
        ya = rng.choice(years, size=n_sims, replace=True)
        yb = rng.choice(years, size=n_sims, replace=True)

    rows = [two_year_sequence(wide, int(a), int(b), start_month) for a, b in zip(ya, yb)]
    ens = pd.DataFrame(rows, columns=col_names)
    ens["year1"] = ya
    ens["year2"] = yb
    ens["total_24mo"] = ens[col_names].sum(axis=1)
    return ens


def ensemble_traces(ens: pd.DataFrame, volume_percentiles=(10, 25, 50, 75, 90)) -> pd.DataFrame:
    """
    Month-by-month percentiles across traces, plus traces whose *24-month volume*
    matches those percentiles (better for a coherent dry/wet sequence).
    """
    month_cols = [c for c in ens.columns if c not in {"year1", "year2", "total_24mo"}]
    monthly_q = ens[month_cols].quantile([p / 100 for p in volume_percentiles])
    monthly_q.index = [f"monthly_p{p:02d}" for p in volume_percentiles]

    volume_rows = {}
    totals = ens["total_24mo"].to_numpy()
    for p in volume_percentiles:
        target = np.quantile(totals, p / 100)
        idx = (np.abs(totals - target)).argmin()
        volume_rows[f"volume_p{p:02d}_trace"] = ens.loc[ens.index[idx], month_cols]
    volume_df = pd.DataFrame(volume_rows).T
    return monthly_q, volume_df, ens["total_24mo"].describe(percentiles=[p / 100 for p in volume_percentiles])


# ---------------------------------------------------------------------------
# Example run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Expected CSV examples:
    #   date,unregulated_inflow_af
    # or
    #   water_year,month,unregulated_inflow_af
    path = "powell_unregulated_inflow.csv"

    monthly = load_inflows(path)
    wide = wy_matrix(monthly, wy_start=2000, wy_end=2026)
    print("Complete water years:", int(wide["complete"].sum()))
    print(wide.loc[wide["complete"], "annual"].describe())

    stats = monthly_percentiles(wide)
    print("\nMonthly climatology (2000–2026 complete WYs), acre-feet:")
    print(stats.round(0))

    most = official_style_trace(stats, scenario="most")
    mn = official_style_trace(stats, scenario="min")
    print("\nOfficial-style Most Probable 24-mo total:", most.sum())
    print("Official-style Probable Minimum 24-mo total:", mn.sum())

    # Exact n^2 permutation ensemble (preferred when n is ~25–30)
    ens = all_year_pair_ensemble(wide, start_month="Oct")
    monthly_q, volume_traces, vol_summary = ensemble_traces(ens)
    print("\n24-month volume distribution from all year-pair permutations:")
    print(vol_summary)

    # Mapping to 24MS language:
    #   Most Probable ~ volume_p50 (or monthly_p50)
    #   Probable Minimum ~ volume_p10 for a single dry 24-mo total
    #                     or mix Y1 monthly_p10 + Y2 monthly_p25 if you want
    #                     to mimic USBR's *constructed* min trace
    most_mc = volume_traces.loc["volume_p50_trace"]
    min_mc = volume_traces.loc["volume_p10_trace"]

    out = pd.DataFrame({
        "official_most": most.values,
        "official_min": mn.values,
        "mc_volume_p50": most_mc.values,
        "mc_volume_p10": min_mc.values,
    }, index=most.index)
    out.to_csv("powell_24ms_inflow_traces_2000_2026.csv")
    ens.to_csv("powell_24ms_all_year_pairs.csv", index=False)
    print("\nWrote powell_24ms_inflow_traces_2000_2026.csv")
