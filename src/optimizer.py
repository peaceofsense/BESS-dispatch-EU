# src/optimizer.py

import pyomo.environ as pyo
from src.battery import Battery


def optimize_day(prices: list[float], battery: Battery) -> dict:
    """
    Stage 1 — Day-Ahead LP optimizer.

    Finds the globally optimal charge/discharge schedule for a single day
    given perfect price foresight and battery physical constraints.

    Args:
        prices:  List of 24 hourly DA prices [€/MWh]
        battery: Battery dataclass with physical parameters

    Returns:
        dict with revenue, charge, discharge, soc schedules
    """

    model = pyo.ConcreteModel()
    #   Sets
    model.H = pyo.Set(initialize=range(24))  # hours 0..23

    #   Parameters
    model.price = pyo.Param(model.H, initialize={h: prices[h] for h in range(24)})
    model.P_max = pyo.Param(initialize=battery.p_max)
    model.E_max = pyo.Param(initialize=battery.e_max)
    model.eta = pyo.Param(initialize=battery.eta)
    model.soc_min = pyo.Param(initialize=battery.soc_min)
    model.soc_init = pyo.Param(initialize=battery.soc_init)
    model.max_cyc = pyo.Param(initialize=battery.max_cycles)

    #   Variables
    model.c = pyo.Var(
        model.H, within=pyo.NonNegativeReals, bounds=(0, battery.p_max)
    )  # charge MW
    model.d = pyo.Var(
        model.H, within=pyo.NonNegativeReals, bounds=(0, battery.p_max)
    )  # discharge MW
    model.soc = pyo.Var(
        model.H, within=pyo.NonNegativeReals, bounds=(battery.soc_min, battery.e_max)
    )  # MWh

    #   Objective function
    def objective_rule(m):
        return sum((m.d[h] - m.c[h]) * m.price[h] for h in m.H)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    #   Constrains

    def soc_hour0_rule(m):  # SOC update — hour 0 starts from soc_init
        return m.soc[0] == m.soc_init + m.c[0] * m.eta - m.d[0] / m.eta

    model.soc_hour0 = pyo.Constraint(rule=soc_hour0_rule)

    def soc_update_rule(m, h):  # SOC update — hours 1..23 follow from previous hour
        if h == 0:
            return pyo.Constraint.Skip
        return m.soc[h] == m.soc[h - 1] + m.c[h] * m.eta - m.d[h] / m.eta

    model.soc_update = pyo.Constraint(model.H, rule=soc_update_rule)

    # Cycle limit — total energy discharged <= max_cycles * E_max
    def cycle_limit_rule(m):
        return sum(m.d[h] for h in m.H) <= m.max_cyc * m.E_max

    model.cycle_limit = pyo.Constraint(rule=cycle_limit_rule)

    # End between 10–50% — not empty, not full
    def soc_terminal_rule(m):
        return pyo.inequality(0.1 * m.E_max, m.soc[23], 0.5 * m.E_max)

    model.soc_terminal = pyo.Constraint(rule=soc_terminal_rule)

    #   Solver
    solver = pyo.SolverFactory("highs")
    result = solver.solve(model, tee=False)

    #   Sanity check
    if (
        result.solver.status != pyo.SolverStatus.ok
        or result.solver.termination_condition != pyo.TerminationCondition.optimal
    ):
        return {
            "status": "infeasible",
            "revenue": 0.0,
            "charge": [0.0] * 24,
            "discharge": [0.0] * 24,
            "soc": [0.0] * 24,
        }

    #   Extract results
    return {
        "status": "optimal",
        "revenue": pyo.value(model.obj),
        "charge": [pyo.value(model.c[h]) for h in range(24)],
        "discharge": [pyo.value(model.d[h]) for h in range(24)],
        "soc": [pyo.value(model.soc[h]) for h in range(24)],
    }
