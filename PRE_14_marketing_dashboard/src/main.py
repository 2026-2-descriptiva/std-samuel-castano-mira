"""Calcula KPIs de marketing a partir de data/campaign_data.csv."""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SUM_COLS = ["impressions", "page_clicks", "paid_clicks", "blocked_clicks", "revenue", "ad_spend", "gross_profit"]


def add_ratios(df):
    """Recalcula razones desde sumas (no promedia razones por fila)."""
    df = df.copy()
    div = lambda a, b: (df[a] / df[b].where(df[b] > 0)).round(4)  # noqa: E731
    df["ctr"] = div("page_clicks", "impressions")
    df["roas"] = div("revenue", "ad_spend")
    df["cpc"] = div("ad_spend", "paid_clicks")
    df["cpa"] = div("ad_spend", "page_clicks")
    df["rpc"] = div("revenue", "paid_clicks")
    df["profit_margin"] = div("gross_profit", "revenue")
    return df


def summarize(df, keys):
    return add_ratios(df.groupby(keys, as_index=False)[SUM_COLS].sum())


def main():
    out = BASE / "submission"
    out.mkdir(exist_ok=True)
    df = pd.read_csv(BASE / "data" / "campaign_data.csv", parse_dates=["utc_date"])
    df["date"] = df["utc_date"].dt.strftime("%Y-%m-%d")

    total = add_ratios(df[SUM_COLS].sum().to_frame().T)
    kpis = total.T.reset_index()
    kpis.columns = ["kpi", "value"]
    kpis.loc[len(kpis)] = ["days", df["date"].nunique()]
    kpis.loc[len(kpis)] = ["rows", len(df)]
    kpis.to_csv(out / "kpis.csv", index=False)

    summarize(df, "date").to_csv(out / "daily_summary.csv", index=False)
    summarize(df, "traffic_source").sort_values("revenue", ascending=False).to_csv(
        out / "source_summary.csv", index=False)
    summarize(df, ["template_name", "traffic_source"]).sort_values("gross_profit", ascending=False).to_csv(
        out / "campaign_summary.csv", index=False)
    print(f"OK: CSV en {out}")


if __name__ == "__main__":
    main()
