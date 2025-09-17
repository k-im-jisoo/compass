# Global Mobility Data Collection & Cleaning Script
# Author: rootless project
#
# This script collects, cleans, and consolidates global mobility data from multiple sources.
# Final output: relocation_data.csv

import requests
import pandas as pd
from bs4 import BeautifulSoup
import pycountry


def get_worldbank_countries(indicator_df):
	# Use the 'Country Name' and 'Country Code' columns from the indicator DataFrame
	countries = indicator_df[['Country Name', 'Country Code']].drop_duplicates()
	# Remove aggregates (e.g., "World", "High income", etc.)
	aggregates = ["World", "High income", "Low income", "Upper middle income", "Lower middle income", "Euro area", "European Union", "OECD members", "Post-demographic dividend", "Pre-demographic dividend", "IDA", "IBRD", "Sub-Saharan Africa", "East Asia & Pacific", "Europe & Central Asia", "Latin America & Caribbean", "Middle East & North Africa", "North America", "South Asia"]
	countries = countries[~countries['Country Name'].isin(aggregates)]
	return countries.reset_index(drop=True)

def map_to_iso3(country_series):
	iso3_codes = []
	for country in country_series:
		try:
			c = pycountry.countries.lookup(country)
			iso3_codes.append(c.alpha_3)
		except LookupError:
			iso3_codes.append(None)
	return pd.DataFrame({'Country Name': country_series, 'Country ISO-3 Code': iso3_codes})

def fetch_indicator(indicator_code):
	url = f'https://api.worldbank.org/v2/en/indicator/{indicator_code}?downloadformat=csv'
	r = requests.get(url)
	if r.status_code != 200:
		raise Exception(f'Failed to fetch indicator {indicator_code}')
	# Find the CSV file link in the zip
	import zipfile, io
	z = zipfile.ZipFile(io.BytesIO(r.content))
	csv_name = [n for n in z.namelist() if n.endswith('.csv') and 'Metadata' not in n][0]
	df = pd.read_csv(z.open(csv_name), skiprows=4)
	return df

def get_latest_indicator(df, value_col_name):
	# Keep only the most recent year with data for each country
	years = [col for col in df.columns if col.isdigit()]
	df['Latest Year'] = df[years].apply(lambda row: row.last_valid_index() if row.last_valid_index() else None, axis=1)
	df['Latest Value'] = df[years].bfill(axis=1).iloc[:, 0]
	return df[['Country Name', 'Country Code', 'Latest Value']].rename(columns={'Latest Value': value_col_name})

def main():

	# 1. Download indicators
	indicators = {
		'SH.MED.BEDS.ZS': 'Hospital Beds',
		'EN.ATM.PM25.MC.M3': 'Air Pollution',
		'SE.SEC.NENR': 'Secondary School Enrollment',
		'SH.DTH.COMM.ZS': 'Disease Mortality',
		'SH.STA.TRAF.P5': 'Traffic Deaths',
	}
	indicator_dfs = {}
	for code, name in indicators.items():
		print(f'Downloading indicator: {name} ({code})...')
		df = fetch_indicator(code)
		indicator_dfs[name] = get_latest_indicator(df, name)

	# 2. Get country list from the first indicator
	print('Extracting country list from World Bank data...')
	first_indicator_df = list(indicator_dfs.values())[0]
	country_df = get_worldbank_countries(first_indicator_df)
	country_df = country_df.rename(columns={"Country Code": "Country ISO-3 Code"})

	# 3. Merge all indicators on ISO-3 code
	print('Merging indicator data...')
	merged = country_df.copy()
	for name, df in indicator_dfs.items():
		merged = pd.merge(merged, df[['Country Code', name]], left_on='Country ISO-3 Code', right_on='Country Code', how='left')
		merged = merged.drop(columns=['Country Code'])

	# 4. Handle missing values
	print('Handling missing values...')
	indicator_cols = list(indicators.values())
	merged = merged.dropna(subset=indicator_cols, how='all')
	for col in indicator_cols:
		merged[col] = merged[col].fillna(merged[col].mean())

	# 5. Round all numeric columns to two decimal places
	num_cols = merged.select_dtypes(include=['float', 'int']).columns
	merged[num_cols] = merged[num_cols].round(2)

	# 6. Save to CSV
	merged.to_csv('relocation_data.csv', index=False)
	print('Saved cleaned data to relocation_data.csv')

if __name__ == '__main__':
	main()
