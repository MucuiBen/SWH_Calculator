#!/usr/bin/env python
# coding: utf-8

# In[1]:
import pandas as pd

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
        if market_pricing is None:
            market_pricing = {'Flat-Plate Collector': 585, 'Vacuum Tubes Collector': 565}
        self.tariff = tariff
        self.grid_emission = grid_emission
        self.lpg_emission = lpg_emission
        self.market_pricing = market_pricing
        self.annual_maintenance_pct = annual_maintenance_pct
        self.installation_pct = installation_pct

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
        if building_type not in HotWaterDemandCalculator.DHWD_VALUES:
            raise ValueError(f"Unknown building type: {building_type}")
        base_demand = HotWaterDemandCalculator.DHWD_VALUES[building_type]
        demand = base_demand * quantity * occupancy_rate
        adjusted_demand = demand * ((desired_temp - 15) / 45)
        return adjusted_demand

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
        self.constants = constants
        self.system_type = system_type
        self.discount_rate = discount_rate
        self.period = period
        self.override_prices = override_prices or {}

    def analyze(self, tank_size, annual_energy_savings):
        cost_per_liter = self.override_prices.get('cost_per_liter', self.constants.market_pricing[self.system_type])
        maintenance_pct = self.override_prices.get('annual_maintenance_pct', self.constants.annual_maintenance_pct)
        install_pct = self.override_prices.get('installation_pct', self.constants.installation_pct)
        tariff = self.override_prices.get('tariff', self.constants.tariff)
        equipment_cost = tank_size * cost_per_liter
        installation_cost = equipment_cost * install_pct
        maintenance_cost_annual = equipment_cost * maintenance_pct
        capex = equipment_cost + installation_cost
        annual_savings = annual_energy_savings * tariff - maintenance_cost_annual
        roi = (annual_savings / capex) * 100 if capex else 0
        payback_period = capex / annual_savings if annual_savings else float('inf')
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
        self.grid_emission_start = grid_emission_start
        self.grid_emission_end = grid_emission_end
        self.lpg_emission = lpg_emission
        self.fuel_type = fuel_type
        self.years = years

    def average_grid_emission(self):
        return (self.grid_emission_start + self.grid_emission_end) / 2

    def calculate_emissions_reduction(self, annual_energy_savings_kwh=None, annual_lpg_savings_kg=None):
        if self.fuel_type == 'electricity':
            ef_kgkwh = self.average_grid_emission()
            return round((annual_energy_savings_kwh or 0) * ef_kgkwh, 2)
        elif self.fuel_type == 'lpg':
            return round((annual_lpg_savings_kg or 0) * self.lpg_emission, 2)
        else:
            raise ValueError("fuel_type must be 'electricity' or 'lpg'")
