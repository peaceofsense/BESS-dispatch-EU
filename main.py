# main.py

from datetime import datetime

import pandas as pd
from src.battery import Battery
from src.optimizer import optimize_day

battery = Battery()  # default 1MW / 2MWh, change params here if needed

# Load data
df = pd.read_csv(
    "data/processed/Germany_Day-ahead_prices_202601010000_202606010000_Hour.csv"
)
df["Time series [h]"] = pd.to_datetime(df["Time series [h]"])
df["date"] = df["Time series [h]"].dt.date

# Running optimzer for each day
results = []

for date, group in df.groupby("date"):
    prices = group["Germany/Luxembourg [€/MWh]"].tolist()

    if len(prices) != 24:  # safety check
        print(f"Skipping {date} — {len(prices)} hours")
        continue

    result = optimize_day(prices, battery)
    result["date"] = date  # tag each result with its date
    result["prices"] = prices
    results.append(result)
    print(f"{date} | status: {result['status']} | revenue: €{result['revenue']:.2f}")

# Creating a dataframe
results_df = pd.DataFrame(
    [
        {
            "date": r["date"],
            "status": r["status"],
            "revenue": r["revenue"],
        }
        for r in results
    ]
)

results_df["date"] = pd.to_datetime(results_df["date"])
results_df["month"] = results_df["date"].dt.to_period("M")

# Save data to file
#
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

results_df.to_csv(f"outputs/daily_revenue_{timestamp}.csv", index=False)

detailed_data = []
for r in results:
    for h in range(24):
        detailed_data.append(
            {
                "date": r["date"],
                "hour": h,
                "price": r["prices"][h],
                "charge": r["charge"][h],
                "discharge": r["discharge"][h],
                "soc": r["soc"][h],
                "status": r["status"],
            }
        )

detailed_df = pd.DataFrame(detailed_data)
detailed_df.to_csv(f"outputs/hourly_detialed_data{timestamp}.csv", index=False)

# Model summary
print("\n--- Monthly Revenue Summary ---")
print(results_df.groupby("month")["revenue"].sum().round(2).to_string())
print(f"\nTotal Q1-Q2 Revenue: €{results_df['revenue'].sum():.2f}")
print(f"Days optimised: {len(results_df)}")
print(f"Infeasible days: {(results_df['status'] == 'infeasible').sum()}")
