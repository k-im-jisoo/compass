# Global Mobility Data Project Report

## Data Sources
- US Embassy List: https://www.usembassy.gov/
- ISO-3 Codes: pycountry library
- World Bank Indicators:
  - SH.MED.BEDS.ZS (Hospital beds)
  - EN.ATM.PM25.MC.M3 (Air pollution)
  - SE.SEC.NENR (Secondary school enrollment)
  - SH.DTH.COMM.ZS (Disease mortality)
  - SH.STA.TRAF.P5 (Traffic deaths)

## Data Collection & Cleaning Process
1. Scraped the US embassy website to get a list of countries with US embassies.
2. Mapped country names to ISO-3 codes using the pycountry library.
3. Downloaded indicator data from the World Bank API for each indicator.
4. For each indicator, selected the most recent available value for each country.
5. Merged all indicators into a single DataFrame using ISO-3 code as the key.
6. Handled missing values by filling with the mean for each indicator.
7. Saved the final tidy dataset as `relocation_data.csv`.

## Key Decisions
- Used the most recent available value for each indicator per country.
- Filled missing indicator values with the mean of that indicator.
- Only included countries with a US embassy in the final dataset.

## Output
- `relocation_data.csv`: Cleaned, unified dataset for analysis.
- `app/data_processing.py`: Script to collect, clean, and consolidate the data.

---

*This report summarizes the data pipeline and key choices for reproducibility and transparency.*
