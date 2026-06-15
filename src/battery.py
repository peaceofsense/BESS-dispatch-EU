from dataclasses import dataclass


@dataclass
class Battery:
    p_max: float = 1.0  # MW
    e_max: float = 2.0  # MWh
    eta: float = 0.92  # one-way efficiency
    soc_min: float = 0.0  # MWh
    soc_init: float = 0.0  # MWh
    max_cycles: float = 1.0
