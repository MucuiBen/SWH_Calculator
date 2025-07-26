# Solar Water Heating Sizing & Economic Analysis Tool

A professional, open-source Streamlit app for sizing solar water heating systems and analyzing their economics and environmental impact—tailored for the Kenyan market and based on the Draft SWH Regulation 2024.

## Features

- **Ward-based solar resource data:** Type-to-search for your admin ward in Kenya and auto-load solar irradiance and temperature data.
- **Flexible input:** Select building type (residential, educational, health, hotel, restaurant, laundry), demand, and system/economic parameters.
- **Live results:** Instantly see collector/tank sizing, CAPEX, OPEX, payback period, ROI, NPV, and carbon savings.
- **Professional UI:** All fonts are Times New Roman. Three clear panels: app description, inputs, and system outputs.
- **Downloadable results:** Export your analysis for reporting.
- **Open-source and extensible.**

## Folder Structure

solar_swh_app/
│
├── app.py # Streamlit UI and logic
├── swh_core.py # Core backend calculations
├── ward_solar_output.csv # Solar data per Kenyan ward
├── requirements.txt # Python dependencies
├── README.md # This file
└── (Optional: GHI.tif, TEMP.tif if raster support is needed)
