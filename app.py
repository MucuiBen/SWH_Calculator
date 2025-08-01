#!/usr/bin/env python
# coding: utf-8

# In[4]:
import streamlit as st
import pandas as pd
import io
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
            font-size: 14px;
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
        .stSelectbox > div[data-baseweb="select"], .stNumberInput input {
            max-width: 220px !important;
            min-width: 120px !important;
        }
        .stSelectbox, .stNumberInput { margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

ward_data = pd.read_csv("ward_solar_output.csv")
ward_list = ward_data['Ward'].sort_values().unique().tolist()

col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

# --- Column 1: App Description & Assumptions ---
with col1:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">Overview of the Calculator</div>
        <ul>
            <li>This Calculator is based on Draft Kenya SWH Regulation of 2024.</li>
            <li>It's tailored for the Kenyan market.</li>
            <li>User or designers can override all parameters except where indicated under assumptions.</li>
            <li>The Tool Calculates system size, Economics Analysis, and CO₂ reduction Potential.</li>
            <li>The Results update as you change your system input parameters.</li>
        </ul>
        <div class="section-header">Key Assumptions</div>
        <ul>
            <li>System Type: <b>Vacuum Tubes Collector</b> (default, not user-editable)</li>
            <li>Installation Cost: <b>20%</b> of equipment cost (not user-editable)</li>
            <li>Annual Maintenance: <b>5%</b> of equipment cost per year (not user-editable)</li>
            <li>Desired Payback Period: <b>5 years</b> (not user-editable)</li>
            <li>Discount/Inflation Rate: <b>8%</b> (not user-editable)</li>
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
        <div class="column-heading">Location and Hot Water Demand Details</div>
    ''', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Clients Location(Admin Ward) :")
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
        st.write("Desired Hot Water Temp (°C) :")
    with c2:
        desired_temp = st.number_input("", min_value=35, max_value=80, value=60, key="desired_temp")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Occupancy rate (%) :")
    with c2:
        occupancy_rate = st.number_input("", min_value=1, max_value=100, value=100, key="occupancy_rate") / 100

    st.markdown('</div>', unsafe_allow_html=True)

# --- Column 3: Inputs Right (Economic & Fuel Type only) ---
with col3:
    st.markdown('''
    <div class="bordered-box">
        <div class="column-heading">Economic & Fuel Inputs</div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Economics</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("SWH Tank Cost (Ksh/liter) :")
    with c2:
        user_cost_per_liter = st.number_input("", min_value=50, max_value=1000, value=565, key="cost_per_liter")  # Default for vacuum tube

    c1, c2 = st.columns([1, 2])
    with c1:
        st.write("Electricity Cost(Ksh/kWh) :")
    with c2:
        user_tariff = st.number_input("", min_value=5.0, max_value=100.0, value=28.69, key="user_tariff")

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

    # Button appears here
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
        # Guard for calculation
        if desired_temp == avg_temp:
            st.error("Desired Hot Water Temp cannot equal Average Ambient Temp.")
            st.stop()
        # Use hidden defaults for system_type, install_pct, maint_pct, finance_years, discount_rate
        system_type = 'Vacuum Tubes Collector'
        installation_pct = 0.20
        maintenance_pct = 0.05
        finance_years = 5
        discount_rate = 0.08

        daily_demand = HotWaterDemandCalculator.calculate_demand(building_type, quantity, desired_temp, occupancy_rate)
        sizing = SystemSizer().size_system(daily_demand, avg_irradiance, avg_temp)
        annual_energy_savings = daily_demand * 365 * 1.162e-3 * (desired_temp - avg_temp)
        econ_result = EconomicAnalyzer(
            system_type=system_type,
            constants=Constants(
                tariff=user_tariff,
                market_pricing={system_type: user_cost_per_liter},
                annual_maintenance_pct=maintenance_pct,
                installation_pct=installation_pct
            ),
            discount_rate=discount_rate,
            period=finance_years
        ).analyze(sizing['tank_size_liters'], annual_energy_savings)
        co2_saved = CarbonEmissionCalculator(
            grid_emission_start=0.425, grid_emission_end=0.25, fuel_type=fuel_type, years=finance_years
        ).calculate_emissions_reduction(annual_energy_savings)

        outputs = [
            ("Hot Water Demand (L/day):", f"{daily_demand:.2f}"),
            ("Collector Area (m²):", f"{sizing['collector_area_m2']}"),
            ("Tank Size (L):", f"{sizing['tank_size_liters']}"),
            ("Equipment Cost (Ksh):", f"{econ_result['equipment_cost']:,}"),
            ("Installation Fee (Ksh):", f"{econ_result['installation_cost']:,}"),
            ("Annual Maintenance (Ksh/yr):", f"{econ_result['maintenance_cost_annual']:,}"),
            ("Total CAPEX (Ksh):", f"{econ_result['capex']:,}"),
            ("Annual Savings (Ksh/yr):", f"{econ_result['annual_savings']:.2f}"),
            ("Payback Period (yrs):", f"{econ_result['payback_period_years']:.2f}"),
            ("ROI (%):", f"{econ_result['roi_percent']:.1f}"),
            (f"NPV ({finance_years}yrs, Ksh):", f"{econ_result['npv_ksh']:.1f}"),
            ("Annual CO₂ Saved (kg):", f"{co2_saved:.1f}"),
        ]
        for label, value in outputs:
            st.markdown(
                f'<div class="output-row"><span class="output-label">{label}</span>'
                f'<span class="output-value">{value}</span></div>',
                unsafe_allow_html=True
            )
        # Download button
        result_df = pd.DataFrame(outputs, columns=['Metric', 'Value'])
        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False)
        st.download_button("Download Results as CSV", csv_buffer.getvalue(), file_name="SWH_outputs.csv", mime="text/csv")
    else:
        st.info("Awaiting complete inputs to calculate...")

    st.markdown('</div>', unsafe_allow_html=True)
