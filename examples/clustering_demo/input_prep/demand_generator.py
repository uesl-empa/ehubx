import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_electrical_demand(
    base_demand=500, seasonal_variation=100, daily_variation=50, randomness=30
):
    # Generate hourly timestamps for the year
    date_rng = pd.date_range(start="2023-01-01 00:00", end="2023-12-31 23:00", freq="H")

    # Time indices for seasonal and daily cycles
    hours_in_year = len(date_rng)
    t_seasonal = np.linspace(0, 2 * np.pi, hours_in_year)  # Yearly cycle
    t_daily = np.linspace(0, 2 * np.pi, 24)  # Daily cycle

    # Seasonal variation (e.g., higher demand in winter and summer due to
    # heating/cooling)
    seasonal_component = seasonal_variation * np.cos(t_seasonal)

    # Daily variation (higher demand in morning and evening)
    daily_cycle = np.tile(np.sin(t_daily) + 1, hours_in_year // 24) * (
        daily_variation / 2
    )

    # Random noise to simulate fluctuations
    noise = np.random.normal(0, randomness, hours_in_year)

    # Total demand calculation
    demand = base_demand + seasonal_component + daily_cycle + noise

    # Create DataFrame
    demand_profile = pd.DataFrame({"datetime": date_rng, "demand_MW": demand})
    demand_profile.index += 1

    return demand_profile


# Directories
model_dir = os.path.abspath(os.path.dirname(__file__))
input_prep_dir = os.path.join(model_dir, "input_prep")
if not os.path.isdir(input_prep_dir):
    os.mkdir(input_prep_dir)

# Save and plot demand
df_dem = generate_electrical_demand()
df_dem.to_csv(os.path.join(input_prep_dir, "demand_el.csv"))
plt.plot(df_dem["datetime"], df_dem["demand_MW"])
plt.show()
