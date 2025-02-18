import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def generate_hourly_price_profile(base_price=50, peak_variation=20,
        season_variation=10, noise_level=5, seed=None):
    """
    Generates an artificial hourly electricity price profile for a year.

    Parameters:
        base_price (float): The average electricity price in currency units.
        peak_variation (float): The peak daily variation in price.
        season_variation (float): The seasonal variation in price.
        noise_level (float): The level of random noise to add.
        seed (int, optional): Random seed for reproducibility.

    Returns:
        pd.DataFrame: A DataFrame with timestamps and corresponding hourly
            prices.
    """
    if seed is not None:
        np.random.seed(seed)

    hours_per_year = 24 * 365
    time_index = pd.date_range(start="2024-01-01", periods=hours_per_year,
                               freq="H")

    # Daily price fluctuation (higher prices during the day, lower at night)
    daily_cycle = peak_variation * np.sin(2 * np.pi * (
        np.arange(hours_per_year) % 24) / 24)

    # Seasonal price fluctuation (higher in winter and summer, lower in spring
    # and fall)
    seasonal_cycle = season_variation * np.sin(
        2 * np.pi * np.arange(hours_per_year) / hours_per_year)

    # Random noise
    noise = np.random.normal(0, noise_level, hours_per_year)

    # Total price calculation
    prices = base_price + daily_cycle + seasonal_cycle + noise

    # Create dataframe
    price_profile = pd.DataFrame({"datetime": time_index, "price": prices})
    price_profile.index += 1

    return price_profile


# Directories
model_dir = os.path.abspath(os.path.dirname(__file__))
input_prep_dir = os.path.join(model_dir, "input_prep")
if not os.path.isdir(input_prep_dir):
    os.mkdir(input_prep_dir)

# Save and plot demand
df_price = generate_hourly_price_profile()
df_price.to_csv(os.path.join(input_prep_dir, "import_price_el.csv"))
plt.plot(df_price["datetime"], df_price["price"])
plt.show()
