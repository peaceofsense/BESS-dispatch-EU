# BESS Day-Ahead Price Arbitrage Optimizer

A linear programming model that optimises the charge/discharge schedule of a Battery Energy Storage System (BESS) against DE-LU day-ahead electricity prices to maximise daily revenue.

---

## What It Does

For each day in the dataset, the optimizer solves an LP problem with perfect price foresight. That finds the best times to charge (buy cheap) and discharge (sell expensive) within the physical constraints of the battery. Results are aggregated into daily and hourly output files.

---

## Data

- **Source:** SMARD (Bundesnetzagentur)
- **Market:** Germany/Luxembourg Day-Ahead prices
- **Period:** 1 January 2026 - 31 May 2026
- **Resolution:** Hourly - 24 price points per day, each representing the DA clearing price for that hour

---

## Battery Parameters (defaults)

| Parameter | Value |
|---|---|
| Power capacity (P_max) | 1 MW |
| Energy capacity (E_max) | 2 MWh |
| One-way efficiency (η) | 0.92 |
| Min. SOC | 0 MWh |
| Initial SOC | 0 MWh |
| Max daily cycles | 1 cycle/day |
| C-rate | 0.5C (2-hour battery) |

Parameters can be overridden when instantiating `Battery()` in `main.py`.

---

## Optimisation Model

- **Solver:** HiGHS (via Pyomo)
- **Objective:** Maximise `Σ (discharge[h] − charge[h]) × price[h]` over 24 hours
- **Decision variables:** Charge MW, Discharge MW, State of Charge MWh per hour

**Constraints:**
- SOC continuity (hour-by-hour energy balance)
- Power limits (0 to P_max for both charge and discharge)
- SOC bounds (soc_min to E_max)
- Daily cycle limit (total discharge ≤ max_cycles × E_max)
- Terminal SOC must be between 10–50% of E_max at end of day

---

## Project Structure

```
├── main.py               # Entry point — loops over each day and runs the optimizer
├── src/
│   ├── battery.py        # Battery dataclass with physical parameters
│   └── optimizer.py      # Pyomo LP model (optimize_day function)
├── data/
│   └── processed/        # Input CSV with hourly DA prices
└── outputs/
    ├── daily_revenue_<timestamp>.csv     # One row per day
    └── hourly_detailed_data<timestamp>.csv  # Price, charge, discharge, SOC per hour
```

---

## Running

```bash
pip install pyomo highspy pandas
python main.py
```

The console prints a per-day status and revenue, followed by a monthly summary and totals at the end.

---

## Output Files

**`daily_revenue_*.csv`**: date, optimisation status, and daily revenue (€)

**`hourly_detailed_data*.csv`**: hour-by-hour breakdown of price, charge, discharge, and SOC for every day

> Full results and analysis are covered in a separate report. (in progress)

---

## Limitations & Notes

- Model assumes **perfect price foresight** (Day-Ahead = oracle): This is an upper-bound benchmark, not a real-time strategy.
- Days with fewer than 24 price entries (e.g. DST transitions) are skipped automatically.
- Degradation costs and grid fees are not included in this version.
