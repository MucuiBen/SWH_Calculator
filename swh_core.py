#!/usr/bin/env python
# coding: utf-8

# In[1]:


# SWH System Core: Improved & Documented (All Classes + Tests + Streamlit Demo)

import pandas as pd
import rasterio
import os
from functools import lru_cache


# In[2]:


# ---- DataLoader Class ----
class DataLoader:
    """
    Loads and queries raster data (irradiance, temperature) for given coordinates.
    Caches queries to avoid re-opening files for repeated lookups.
    """
    def __init__(self, ghi_file, temp_file):
        self.ghi_file = ghi_file
        self.temp_file = temp_file

    @lru_cache(maxsize=128)
    def get_solar_irradiance_temp(self, lat, lon):
        """
        Returns solar irradiance and temperature for given latitude/longitude.
        """
        try:
            with rasterio.open(self.ghi_file) as ghi_src:
                row, col = ghi_src.index(lon, lat)
                ghi = ghi_src.read(1, window=((row, row+1), (col, col+1))).mean()
            with rasterio.open(self.temp_file) as temp_src:
                row, col = temp_src.index(lon, lat)
                temp = temp_src.read(1, window=((row, row+1), (col, col+1))).mean()
            return {'irradiance': round(ghi, 2), 'temperature': round(temp, 2)}
        except Exception as e:
            raise ValueError(f"Data loading failed for ({lat},{lon}): {e}")


# In[3]:


# ---- Constants Class ----
class Constants:
    """
    Holds default and user-overridable constants for system sizing and economics.
    """
    def __init__(self, 
                 tariff=28.69, 
                 grid_emission=0.425, 
                 lpg_emission=3.0,   # kg CO2 per kg LPG
                 market_pricing=None, 
                 annual_maintenance_pct=0.05,
                 installation_pct=0.20):
        """
        Parameters:
            tariff: Default electricity tariff (Ksh/kWh)
            grid_emission: Grid emission factor (tonnes CO2/MWh)
            lpg_emission: LPG emission factor (kg CO2/kg)
            market_pricing: Dict of system type to price per liter (Ksh/liter)
            annual_maintenance_pct: Annual maintenance as % of equipment cost
            installation_pct: Installation as % of equipment cost
        """
        if market_pricing is None:
            market_pricing = {'Flat-Plate Collector': 585, 'Vacuum Tubes Collector': 565} # Solargen technologies 
        self.tariff = tariff
        self.grid_emission = grid_emission
        self.lpg_emission = lpg_emission
        self.market_pricing = market_pricing
        self.annual_maintenance_pct = annual_maintenance_pct
        self.installation_pct = installation_pct


# In[4]:


# ---- HotWaterDemandCalculator Class ----
class HotWaterDemandCalculator:
    """
    Calculates daily hot water demand for various building types and use cases.
    """
    DHWD_VALUES = {
        "residential": 30,        # liters/person
        "educational": 5,         # liters/student
        "health": 50,             # liters/bed
        "commercial_hotel": 40,   # liters/bed
        "restaurant": 5,          # liters/meal
        "laundry": 5              # liters/kg laundry
    }

    @staticmethod
    def calculate_demand(building_type, quantity, desired_temp=60, occupancy_rate=1.0):
        """
        building_type: e.g. 'residential', 'laundry'
        quantity: number of people, beds, meals, or kg laundry as relevant
        desired_temp: output hot water temp (°C)
        occupancy_rate: (0-1), for seasonal buildings
        Returns adjusted daily demand in liters.
        """
        if building_type not in HotWaterDemandCalculator.DHWD_VALUES:
            raise ValueError(f"Unknown building type: {building_type}")
        base_demand = HotWaterDemandCalculator.DHWD_VALUES[building_type]
        demand = base_demand * quantity * occupancy_rate
        adjusted_demand = demand * ((desired_temp - 15) / 45)
        return adjusted_demand


# In[5]:


# ---- SystemSizer Class ----
class SystemSizer:
    """
    Calculates required collector area and tank size for an SWH system.
    """
    SPECIFIC_HEAT_WATER_KWH = 1.162e-3  # kWh/liter/°C

    def __init__(self, efficiency=0.65, storage_loss=0.10):
        self.efficiency = efficiency
        self.storage_loss = storage_loss

    def size_system(self, daily_demand, solar_irradiance, inlet_temp):
        """
        Calculates collector area and tank size.
        Returns dict with keys 'collector_area_m2', 'tank_size_liters'.
        """
        if solar_irradiance <= 0 or self.efficiency <= 0:
            raise ValueError("Irradiance and efficiency must be > 0.")
        required_energy = daily_demand * self.SPECIFIC_HEAT_WATER_KWH * (60 - inlet_temp)
        effective_energy = required_energy / (self.efficiency * (1 - self.storage_loss))
        collector_area = effective_energy / solar_irradiance
        tank_size = daily_demand * 1.2  # 20% oversize
        return {
            "collector_area_m2": round(collector_area, 2),
            "tank_size_liters": round(tank_size, 2)
        }


# In[6]:


# ---- EconomicAnalyzer Class ----
class EconomicAnalyzer:
    """
    Performs economic analysis: CAPEX, savings, ROI, payback, and NPV.
    """
    def __init__(self, 
                 system_type='Vacuum Tubes Collector', 
                 constants=Constants(), 
                 discount_rate=0.08, 
                 period=7, 
                 override_prices=None):
        """
        system_type: SWH type (e.g., 'Vacuum Tubes Collector')
        constants: Constants object
        discount_rate: NPV discount rate (decimal, e.g. 0.08 for 8%)
        period: NPV/payback period in years
        override_prices: dict for price/maintenance/installation if user overrides
        """
        self.constants = constants
        self.system_type = system_type
        self.discount_rate = discount_rate
        self.period = period
        self.override_prices = override_prices or {}

    def analyze(self, tank_size, annual_energy_savings):
        """
        Returns full breakdown:
        - equipment_cost
        - installation_cost
        - maintenance_cost_annual
        - capex (equipment + install)
        - annual_savings
        - ROI (%)
        - Payback (years)
        - NPV (Ksh)
        """
        # Get prices (override if provided)
        cost_per_liter = self.override_prices.get('cost_per_liter', self.constants.market_pricing[self.system_type])
        maintenance_pct = self.override_prices.get('annual_maintenance_pct', self.constants.annual_maintenance_pct)
        install_pct = self.override_prices.get('installation_pct', self.constants.installation_pct)
        tariff = self.override_prices.get('tariff', self.constants.tariff)
        # Costs
        equipment_cost = tank_size * cost_per_liter
        installation_cost = equipment_cost * install_pct
        maintenance_cost_annual = equipment_cost * maintenance_pct
        capex = equipment_cost + installation_cost
        annual_savings = annual_energy_savings * tariff - maintenance_cost_annual
        roi = (annual_savings / capex) * 100 if capex else 0
        payback_period = capex / annual_savings if annual_savings else float('inf')
        # NPV calculation
        npv = -capex
        for year in range(1, self.period+1):
            npv += annual_savings / ((1+self.discount_rate) ** year)
        return {
            "equipment_cost": round(equipment_cost, 2),
            "installation_cost": round(installation_cost, 2),
            "maintenance_cost_annual": round(maintenance_cost_annual, 2),
            "capex": round(capex, 2),
            "annual_savings": round(annual_savings, 2),
            "roi_percent": round(roi, 2),
            "payback_period_years": round(payback_period, 2),
            "npv_ksh": round(npv, 2)
        }


# In[7]:


# ---- CarbonEmissionCalculator Class ----
class CarbonEmissionCalculator:
    """
    Calculates annual CO2 savings for electricity, LPG, or other fuels.
    Supports emission factor change over system lifetime.
    """
    def __init__(self, 
                 grid_emission_start=0.425, 
                 grid_emission_end=0.25, 
                 lpg_emission=3.0, 
                 fuel_type='electricity', 
                 years=10):
        """
        grid_emission_start: starting EF (ton/MWh)
        grid_emission_end: ending EF after years (ton/MWh)
        lpg_emission: kg CO2/kg LPG
        fuel_type: 'electricity' or 'lpg'
        years: for time-varying EF
        """
        self.grid_emission_start = grid_emission_start
        self.grid_emission_end = grid_emission_end
        self.lpg_emission = lpg_emission
        self.fuel_type = fuel_type
        self.years = years

    def average_grid_emission(self):
        # Linear reduction over period
        return (self.grid_emission_start + self.grid_emission_end) / 2

    def calculate_emissions_reduction(self, annual_energy_savings_kwh=None, annual_lpg_savings_kg=None):
        """
        For electricity: annual_energy_savings_kwh required
        For LPG: annual_lpg_savings_kg required
        Returns kgCO2/year (or total over period if needed)
        """
        if self.fuel_type == 'electricity':
            ef_kgkwh = self.average_grid_emission() * 1000 / 1000  # ton/MWh to kg/kWh
            return round((annual_energy_savings_kwh or 0) * ef_kgkwh, 2)
        elif self.fuel_type == 'lpg':
            return round((annual_lpg_savings_kg or 0) * self.lpg_emission, 2)
        else:
            raise ValueError("fuel_type must be 'electricity' or 'lpg'")


# In[8]:


# --- Example Test Cases (with unittest) ---
import unittest

class TestSWH(unittest.TestCase):
    def setUp(self):
        self.constants = Constants()
        self.dataloader = DataLoader('GHI.tif', 'TEMP.tif')
        self.hw_calc = HotWaterDemandCalculator()
        self.sizer = SystemSizer()
        self.econ = EconomicAnalyzer(constants=self.constants)
        self.co2 = CarbonEmissionCalculator()

    def test_demand_calc(self):
        self.assertAlmostEqual(
            self.hw_calc.calculate_demand('residential', 4, 60, 1.0),
            120.0
        )

    def test_system_sizer(self):
        out = self.sizer.size_system(120, 5.0, 20)
        self.assertIn('collector_area_m2', out)

    def test_economic_analyzer(self):
        out = self.econ.analyze(144, 800)
        self.assertIn('capex', out)
        self.assertIn('npv_ksh', out)

    def test_carbon(self):
        saved = self.co2.calculate_emissions_reduction(1000)
        self.assertGreater(saved, 0)

unittest.main(argv=[''], verbosity=2, exit=False)  # Uncomment to run in notebook


# In[9]:



# --- Streamlit Example UI (snippet for your app.py) ---
# Uncomment this for your streamlit app!
'''
import streamlit as st
import pandas as pd
from swh_core import (
    DataLoader, Constants, HotWaterDemandCalculator, 
    SystemSizer, EconomicAnalyzer, CarbonEmissionCalculator
)

ward_df = pd.read_csv("ward_solar_output.csv")

st.title("Solar Water Heating Sizing Tool")

# Admin Ward search (not dropdown)
ward_input = st.text_input("Enter Admin Ward Name:")
filtered = ward_df[ward_df['Ward'].str.contains(ward_input, case=False)] if ward_input else pd.DataFrame()

if not filtered.empty:
    ward_row = filtered.iloc[0]
    irradiance = ward_row['Irradiance_kWh/m2/day']
    ambient_temp = ward_row['Ambient_Temperature_C']
    st.success(f"Loaded solar data for {ward_row['Ward']}. GHI={irradiance}, Temp={ambient_temp}")
    # Remaining UI: system config, run model, show charts, allow PDF/CSV download, plot payback chart...

if st.button("Download Results"):
    st.download_button("Download as CSV", ward_df.to_csv(index=False), "results.csv")
# (Add PDF export as needed)
'''

