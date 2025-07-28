#!/usr/bin/env python
# coding: utf-8

# In[4]:
import streamlit as st
import pandas as pd
from swh_core import (
    Constants, HotWaterDemandCalculator, SystemSizer, EconomicAnalyzer, CarbonEmissionCalculator
)

st.set_page_config(page_title="Solar Water Heating Sizing Calculator", layout="wide")

st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Times New Roman', Times, serif !important;
            font-size: 14px !important;
        }
        .main-title {
            font-size: 20px !important;
            font-weight: bold !important;
        }
        .column-heading {
            font-size: 24px !important;
            font-weight: bold !important;
            font-family: 'Times New Roman', Times, serif !important;
            text-align: left !important;
            margin-bottom: 15px;
        }
        .section-header {
            font-size: 18px !important;
            font-weight: bold !important;
            font-family: 'Times New Roman', Times, serif !important;
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
            color: #002147 !important;
        }
        /* Reduce width of all select and number inputs */
        .stSelectbox > div[data-baseweb="select"], .stNumberInput input {
            max-width: 220px !important;
            min-width: 120px !important;
        }
        .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

ward_data = pd.read_csv("ward_solar_output.csv")
ward_list = ward_data['Ward'].sort_values().unique().tolist()

# --- 4 Columns: Description, Inputs-Left, Inputs-Right, Outputs ---
col1, col2, col3, col4 = st.columns([1, 2, 2, 2])

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

# --- Input States ---
state = st.session_state
if "run_btn" not in state:
    state.run_btn = False

# --- Column 2: Inputs Left (Location + Hot Water Demand) ---
with col2:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">General & Demand Inputs</div>
    ''', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Admin Ward :")
    with c2:
        ward_selected_name = st.selectbox("", ward_list, key="ward_select")
    ward_selected = ward_data[ward_data['Ward'] == ward_selected_name].iloc[0] if ward_selected_name else None

    st.markdown('<div class="section-header">Hot Water Demand</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Building Type :")
    with c2:
        building_type = st.selectbox("", ['residential', 'educational', 'health', 'commercial_hotel', 'restaurant', 'laundry'], key="build_type")

    quantity_label = {
        'residential': 'People :',
        'educational': 'Students :',
        'health': 'Beds :',
        'commercial_hotel': 'Beds :',
        'restaurant': 'Meals/day :',
        'laundry': 'Kg laundry/day :'
    }[building_type]
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write(quantity_label)
    with c2:
        quantity = st.number_input("", min_value=1, value=4, key="quantity")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Hot Water Temp (°C) :")
    with c2:
        desired_temp = st.number_input("", min_value=35, max_value=80, value=60, key="desired_temp")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Occupancy (%) :")
    with c2:
        occupancy_rate = st.number_input("", min_value=1, max_value=100, value=100, key="occupancy_rate") / 100

    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 3: Inputs Right (System, Economic & Fuel Type) ---
with col3:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">System & Economic Inputs</div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-header">System</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("SWH System Type :")
    with c2:
        system_type = st.selectbox("", ['Flat-Plate Collector', 'Vacuum Tubes Collector'], key="system_type")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Tank Cost (Ksh/liter) :")
    with c2:
        user_cost_per_liter = st.number_input("", min_value=50, max_value=1000, value=585 if system_type == 'Flat-Plate Collector' else 565, key="cost_per_liter")

    st.markdown('<div class="section-header">Economics</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Electricity Tariff (Ksh/kWh) :")
    with c2:
        user_tariff = st.number_input("", min_value=5.0, max_value=100.0, value=28.69, key="user_tariff")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Installation (%) :")
    with c2:
        user_install_pct = st.number_input("", min_value=0, max_value=50, value=20, key="install_pct") / 100

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Annual Maintenance (%) :")
    with c2:
        user_maint_pct = st.number_input("", min_value=0, max_value=20, value=5, key="maint_pct") / 100

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("NPV/Payback (years) :")
    with c2:
        finance_years = st.number_input("", min_value=1, max_value=15, value=7, key="finance_years")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Discount Rate (%) :")
    with c2:
        discount_rate = st.number_input("", min_value=1, max_value=20, value=8, key="discount_rate") / 100

    st.markdown('<div class="section-header">Fuel Type</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Fuel Replaced :")
    with c2:
        fuel_type = st.selectbox("", ['electricity', 'lpg'], key="fuel_type")

    if fuel_type == 'electricity':
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("Grid Start Emission Factor (ton/MWh) :")
        with c2:
            grid_emission_start = st.number_input("", min_value=0.2, max_value=1.0, value=0.425, key="grid_ef_start")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("Grid End Emission Factor (ton/MWh) :")
        with c2:
            grid_emission_end = st.number_input("", min_value=0.1, max_value=1.0, value=0.25, key="grid_ef_end")
        lpg_emission = None
        annual_lpg_savings = None
    else:
        grid_emission_start = None
        grid_emission_end = None
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("LPG Emission Factor (kgCO2/kg) :")
        with c2:
            lpg_emission = st.number_input("", min_value=1.0, max_value=5.0, value=3.0, key="lpg_emission")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("Annual LPG Savings (kg/year) :")
        with c2:
            annual_lpg_savings = st.number_input("", min_value=1, max_value=5000, value=5000, key="lpg_savings")

    # Dedicated button in this column
    state.run_btn = st.button("Run Full Analysis")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 4: Outputs ---
with col4:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">System Outputs</div>
    ''', unsafe_allow_html=True)
    if state.run_btn and ward_selected is not None:
        avg_irradiance = ward_selected['Irradiance_kWh/m2/day']
        avg_temp = ward_selected['Ambient_Temperature_C']
        st.markdown(
            f'<div class="metric-row"><span class="metric-label">Avg Irradiance (kWh/m²/day):</span>'
            f'<span class="metric-value">{avg_irradiance}</span></div>', unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="metric-row"><span class="metric-label">Avg Ambient Temp (°C):</span>'
            f'<span class="metric-value">{avg_temp}</span></div>', unsafe_allow_html=True
        )
        # Calculations
        daily_demand = HotWaterDemandCalculator.calculate_demand(building_type, quantity, desired_temp, occupancy_rate)
        sizing = SystemSizer().size_system(daily_demand, avg_irradiance, avg_temp)
        annual_energy_savings = daily_demand * 365 * 1.162e-3 * (desired_temp - avg_temp)
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
