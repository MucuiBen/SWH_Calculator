#!/usr/bin/env python
# coding: utf-8

# In[4]:
import streamlit as st
import pandas as pd
from swh_core import (
    Constants, HotWaterDemandCalculator, SystemSizer, EconomicAnalyzer, CarbonEmissionCalculator
)

st.set_page_config(page_title="Solar Water Heating Sizing Tool", layout="wide")

# --- Custom CSS ---
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
            text-align: left !important;
            margin-bottom: 15px;
        }
        .section-header {
            font-size: 18px !important;
            font-weight: bold !important;
            margin-top: 10px;
            text-align: left !important;
        }
        .bordered-box {
            border: 3px solid #4682B4;
            padding: 18px 16px 16px 16px;
            border-radius: 12px;
            background-color: #81D5FB;
            margin-bottom: 20px;
        }
        .output-row {
            display: flex;
            flex-direction: row;
            align-items: center;
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
            color: #002147 !important;
        }
    </style>
""", unsafe_allow_html=True)

ward_data = pd.read_csv("ward_solar_output.csv")
ward_list = ward_data['Ward'].sort_values().unique().tolist()

col1, col2, col3 = st.columns([1, 3, 2])

# --- Column 1: App Description ---
with col1:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">App Description</div>
        <ul>
            <li>This Calculator is based on Draft Kenya SWH Regulation of 2024.</li>
            <li>It's tailored for the Kenyan market.</li>
            <li>User or designers can override all parameters.</li>
            <li>The Tool Calculates system size, Economics Analysis, and CO₂ reduction Potential.</li>
            <li>The Results update as you change your system input Paramters.</li>
        </ul>
    </div>
    ''', unsafe_allow_html=True)

# --- Column 2: Inputs ---
with col2:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">Select Required Inputs</div>
    ''', unsafe_allow_html=True)

    # Location: Dropdown with search
    row1c1, row1c2 = st.columns([1, 3])
    with row1c1:
        st.markdown("Admin Ward :")
    with row1c2:
        ward_selected_name = st.selectbox("", ward_list, key="ward_select")
    ward_selected = ward_data[ward_data['Ward'] == ward_selected_name].iloc[0] if ward_selected_name else None
    if ward_selected is not None:
        irradiance = ward_selected['Irradiance_kWh/m2/day']
        ambient_temp = ward_selected['Ambient_Temperature_C']
    else:
        irradiance, ambient_temp = None, None

    st.markdown('<div class="section-header">Hot Water Demand Input Parameters</div>', unsafe_allow_html=True)
    # Horizontal for Building Type
    row2c1, row2c2 = st.columns([1, 3])
    with row2c1:
        st.markdown("Building Type :")
    with row2c2:
        building_type = st.selectbox("", ['residential', 'educational', 'health', 'commercial_hotel', 'restaurant', 'laundry'])
    quantity_label = {
        'residential': 'People',
        'educational': 'Students',
        'health': 'Beds',
        'commercial_hotel': 'Beds',
        'restaurant': 'Meals/day',
        'laundry': 'Kg laundry/day'
    }[building_type]
    row3c1, row3c2 = st.columns([1, 3])
    with row3c1:
        st.markdown(f"{quantity_label} :")
    with row3c2:
        quantity = st.number_input("", min_value=1, value=4)
    row4c1, row4c2 = st.columns([1, 3])
    with row4c1:
        st.markdown("Hot Water Temp (°C) :")
    with row4c2:
        desired_temp = st.number_input("", min_value=35, max_value=80, value=60)
    row5c1, row5c2 = st.columns([1, 3])
    with row5c1:
        st.markdown("Occupancy (%) :")
    with row5c2:
        occupancy_rate = st.number_input("", min_value=1, max_value=100, value=100) / 100

    st.markdown('<div class="section-header">System Type & Economic Inputs Parameters</div>', unsafe_allow_html=True)
    row6c1, row6c2 = st.columns([1, 3])
    with row6c1:
        st.markdown("SWH System Type :")
    with row6c2:
        system_type = st.selectbox("", ['Flat-Plate Collector', 'Vacuum Tubes Collector'])
    row7c1, row7c2 = st.columns([1, 3])
    with row7c1:
        st.markdown("Electricity Tariff (Ksh/kWh) :")
    with row7c2:
        user_tariff = st.number_input("", min_value=5.0, max_value=100.0, value=28.69)
    row8c1, row8c2 = st.columns([1, 3])
    with row8c1:
        st.markdown("Tank Cost (Ksh/liter) :")
    with row8c2:
        user_cost_per_liter = st.number_input("", min_value=50, max_value=1000, value=585 if system_type == 'Flat-Plate Collector' else 565)
    row9c1, row9c2 = st.columns([1, 3])
    with row9c1:
        st.markdown("Installation (%) :")
    with row9c2:
        user_install_pct = st.number_input("", min_value=0, max_value=50, value=20) / 100
    row10c1, row10c2 = st.columns([1, 3])
    with row10c1:
        st.markdown("Annual Maintenance (%) :")
    with row10c2:
        user_maint_pct = st.number_input("", min_value=0, max_value=20, value=5) / 100
    row11c1, row11c2 = st.columns([1, 3])
    with row11c1:
        st.markdown("NPV/Payback (years) :")
    with row11c2:
        finance_years = st.number_input("", min_value=1, max_value=15, value=7)
    row12c1, row12c2 = st.columns([1, 3])
    with row12c1:
        st.markdown("Discount Rate (%) :")
    with row12c2:
        discount_rate = st.number_input("", min_value=1, max_value=20, value=8) / 100

    st.markdown('<div class="section-header">Fuel Type</div>', unsafe_allow_html=True)
    row13c1, row13c2 = st.columns([1, 3])
    with row13c1:
        st.markdown("Fuel Replaced :")
    with row13c2:
        fuel_type = st.selectbox("", ['electricity', 'lpg'])
    if fuel_type == 'electricity':
        row14c1, row14c2 = st.columns([1, 3])
        with row14c1:
            st.markdown("Grid Start Emission Factor (ton/MWh) :")
        with row14c2:
            grid_emission_start = st.number_input("", min_value=0.2, max_value=1.0, value=0.425)
        row15c1, row15c2 = st.columns([1, 3])
        with row15c1:
            st.markdown("Grid End Emission Factor (ton/MWh) :")
        with row15c2:
            grid_emission_end = st.number_input("", min_value=0.1, max_value=1.0, value=0.25)
    else:
        grid_emission_start = None
        grid_emission_end = None
    if fuel_type == 'lpg':
        row16c1, row16c2 = st.columns([1, 3])
        with row16c1:
            st.markdown("LPG Emission Factor (kgCO2/kg) :")
        with row16c2:
            lpg_emission = st.number_input("", min_value=1.0, max_value=5.0, value=3.0)
        row17c1, row17c2 = st.columns([1, 3])
        with row17c1:
            st.markdown("Annual LPG Savings (kg/year) :")
        with row17c2:
            annual_lpg_savings = st.number_input("", min_value=1, max_value=5000, value=5000)
    else:
        lpg_emission = None
        annual_lpg_savings = None

    run_btn = st.button("Run Full Analysis")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 3: Outputs ---
with col3:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">System Outputs</div>
    ''', unsafe_allow_html=True)

    # Show GHI and Temp as separate output values (on top)
    if irradiance is not None and ambient_temp is not None:
        st.markdown(
            f'<div class="output-row"><span class="output-label">Avg Irradiance (kWh/m²/day):</span>'
            f'<span class="output-value">{irradiance}</span></div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="output-row"><span class="output-label">Avg Ambient Temp (°C):</span>'
            f'<span class="output-value">{ambient_temp}</span></div>',
            unsafe_allow_html=True
        )

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
            period=int(finance_years)
        ).analyze(sizing['tank_size_liters'], annual_energy_savings)

        co2_saved = CarbonEmissionCalculator(
            grid_emission_start=0.425, grid_emission_end=0.25, fuel_type=fuel_type, years=int(finance_years)
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
