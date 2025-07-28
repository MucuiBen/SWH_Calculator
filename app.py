#!/usr/bin/env python
# coding: utf-8

# In[4]:
import streamlit as st
import pandas as pd
from swh_core import (
    Constants, HotWaterDemandCalculator, SystemSizer, EconomicAnalyzer, CarbonEmissionCalculator
)

st.set_page_config(page_title="Solar Water Heating Sizing Tool", layout="wide")

# --- Custom CSS for Times New Roman fonts and borders ---
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Times New Roman', Times, serif !important;
            font-size: 18px !important;
        }
        .main-title {
            font-size: 20px !important;
            font-weight: bold !important;
        }
        .column-heading {
            font-size: 20px !important;
            font-weight: bold !important;
            font-family: 'Times New Roman', Times, serif !important;
            text-align: center;
            margin-bottom: 15px;
        }
        .section-header {
            font-size: 18px !important;
            font-weight: bold !important;
            font-family: 'Times New Roman', Times, serif !important;
            margin-top: 10px;
        }
        .bordered-box {
            border: 3px solid #4682B4;
            padding: 18px 16px 16px 16px;
            border-radius: 12px;
            background-color: #F8F9FA;
            margin-bottom: 20px;
        }
        .output-row {
            display: flex;
            flex-direction: row;
            align-items: center;
            font-family: 'Times New Roman', Times, serif !important;
            margin-bottom: 12px;
        }
        .output-label {
            min-width: 250px;
            font-weight: bold;
            font-size: 18px;
        }
        .output-value {
            display: inline-block;
            font-size: 14px;
            background: #e9f3ff;
            border: 2px solid #4682B4;
            border-radius: 6px;
            padding: 2px 18px;
            margin-left: 16px;
            font-family: 'Times New Roman', Times, serif !important;
            color: #002147 !important; /* Navy Blue */
        }
    </style>
""", unsafe_allow_html=True)

ward_data = pd.read_csv("ward_solar_output.csv")

col1, col2, col3 = st.columns([2, 2, 3])

# --- Column 1: App Description ---
with col1:
    st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
    st.markdown('<div class="column-heading">App Description</div>', unsafe_allow_html=True)
    st.markdown("""
    <ul>
      <li>Based on Draft SWH Regulation 2024.</li>
      <li>Tailored for the Kenyan market and regulations.</li>
      <li>User can override all parameters.</li>
      <li>Calculates system size, economics, and CO₂ reduction.</li>
      <li>Results update as you change your inputs.</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 2: Inputs ---
with col2:
    st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
    st.markdown('<div class="column-heading">Select Required Inputs</div>', unsafe_allow_html=True)

    # Location
    ward_query = st.text_input("Search Admin Ward", "")
    matches = ward_data[ward_data['Ward'].str.contains(ward_query, case=False, na=False)]
    ward_selected = matches.iloc[0] if len(matches) == 1 else None

    if ward_selected is not None:
        irradiance = ward_selected['Irradiance_kWh/m2/day']
        ambient_temp = ward_selected['Ambient_Temperature_C']
        st.success(f"Loaded: {ward_selected['Ward']} (GHI={irradiance}, Temp={ambient_temp})")
    else:
        irradiance, ambient_temp = None, None

    # --- Hot Water Demand Inputs
    st.markdown('<div class="section-header">Hot Water Demand Input Parameters</div>', unsafe_allow_html=True)
    building_type = st.selectbox("Building Type", ['residential', 'educational', 'health', 'commercial_hotel', 'restaurant', 'laundry'])
    quantity_label = {
        'residential': 'People',
        'educational': 'Students',
        'health': 'Beds',
        'commercial_hotel': 'Beds',
        'restaurant': 'Meals/day',
        'laundry': 'Kg laundry/day'
    }[building_type]
    quantity = st.number_input(quantity_label, 1, value=4)
    desired_temp = st.slider("Hot Water Temp (°C)", 35, 80, 60)
    occupancy_rate = st.slider("Occupancy (%)", 50, 100, 100) / 100

    # --- System & Economic Inputs
    st.markdown('<div class="section-header">System Type & Economic Inputs Parameters</div>', unsafe_allow_html=True)
    system_type = st.selectbox("SWH System Type", ['Flat-Plate Collector', 'Vacuum Tubes Collector'])
    user_tariff = st.number_input("Electricity Tariff (Ksh/kWh)", 5.0, 100.0, 28.69)
    user_cost_per_liter = st.number_input("Tank Cost (Ksh/liter)", 50, 1000, 585 if system_type == 'Flat-Plate Collector' else 565)
    user_install_pct = st.slider("Installation (%)", 0, 50, 20) / 100
    user_maint_pct = st.slider("Annual Maintenance (%)", 0, 20, 5) / 100
    finance_years = st.slider("NPV/Payback (years)", 1, 15, 7)
    discount_rate = st.slider("Discount Rate (%)", 1, 20, 8) / 100

    # --- Fuel Type
    st.markdown('<div class="section-header">Fuel Type</div>', unsafe_allow_html=True)
    fuel_type = st.selectbox("Fuel Replaced", ['electricity', 'lpg'])
    grid_emission_start = st.number_input("Grid Start Emission Factor (ton/MWh)", 0.2, 1.0, 0.425) if fuel_type == 'electricity' else None
    grid_emission_end = st.number_input("Grid End Emission Factor (ton/MWh)", 0.1, 1.0, 0.25) if fuel_type == 'electricity' else None
    lpg_emission = st.number_input("LPG Emission Factor (kgCO2/kg)", 1.0, 5.0, 3.0) if fuel_type == 'lpg' else None
    annual_lpg_savings = st.number_input("Annual LPG Savings (kg/year)", 1, 5000, 5000) if fuel_type == 'lpg' else None

    run_btn = st.button("Run Full Analysis")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 3: Outputs ---
with col3:
    st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
    st.markdown('<div class="column-heading">System Outputs</div>', unsafe_allow_html=True)
    if run_btn and irradiance is not None and ambient_temp is not None:
        daily_demand = HotWaterDemandCalculator.calculate_demand(building_type, quantity, desired_temp, occupancy_rate)
        sizing = SystemSizer().size_system(daily_demand, irradiance, ambient_temp)
        annual_energy_savings = daily_demand * 365 * 1.162e-3 * (desired_temp - ambient_temp)
        econ_result = EconomicAnalyzer(
            system_type=system_type,
            constants=Constants(
                tariff=user_tariff,
                market_pricing={system_type: user_cost_per_liter},
                annual_maintenance_pct=user_maint_pct,
                installation_pct=user_install_pct
            ),
            discount_rate=discount_rate,
            period=finance_years
        ).analyze(sizing['tank_size_liters'], annual_energy_savings)

        co2_saved = CarbonEmissionCalculator(
            grid_emission_start=0.425, grid_emission_end=0.25, fuel_type=fuel_type, years=finance_years
        ).calculate_emissions_reduction(annual_energy_savings)

        outputs = [
            ("Hot Water Demand (L/day)", f"{daily_demand:.2f}"),
            ("Collector Area (m²)", f"{sizing['collector_area_m2']}"),
            ("Tank Size (L)", f"{sizing['tank_size_liters']}"),
            ("Equipment Cost (Ksh)", f"{econ_result['equipment_cost']:,}"),
            ("Installation Fee (Ksh)", f"{econ_result['installation_cost']:,}"),
            ("Annual Maintenance (Ksh/yr)", f"{econ_result['maintenance_cost_annual']:,}"),
            ("Total CAPEX (Ksh)", f"{econ_result['capex']:,}"),
            ("Annual Savings (Ksh/yr)", f"{econ_result['annual_savings']:.2f}"),
            ("Payback (yrs)", f"{econ_result['payback_period_years']:.2f}"),
            ("ROI (%)", f"{econ_result['roi_percent']:.1f}"),
            (f"NPV ({finance_years}yrs, Ksh)", f"{econ_result['npv_ksh']:.1f}"),
            ("Annual CO₂ Saved (kg)", f"{co2_saved:.1f}"),
        ]
        for label, value in outputs:
            st.markdown(
                f'<div class="output-row"><span class="output-label">{label}:</span>'
                f'<span class="output-value">{value}</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Awaiting complete inputs to calculate...")

    st.markdown('</div>', unsafe_allow_html=True)
