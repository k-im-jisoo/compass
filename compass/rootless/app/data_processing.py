# Global Mobility Data Collection & Cleaning Script
# Author: rootless project
#
# This script collects, cleans, and consolidates global mobility data from multiple sources.
# Final output: relocation_data.csv

import requests
import pandas as pd
from bs4 import BeautifulSoup
import pycountry

def get_embassy_countries():
	url = 'https://www.usembassy.gov/'
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser')
	country_list = []
	for link in soup.select('section#embassy-list a'):  # Main embassy list section
		country = link.get_text(strip=True)
		if country and country not in country_list:
			country_list.append(country)
	return pd.Series(country_list, name='Country Name')

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
	# 1. Get country list
	print('Collecting country list from US Embassy website...')
	countries = get_embassy_countries()
	print(f'Found {len(countries)} countries.')

	# 2. Map to ISO-3 codes
	print('Mapping countries to ISO-3 codes...')
	country_df = map_to_iso3(countries)

	# 3. Download indicators
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

	# 4. Merge all indicators on ISO-3 code
	print('Merging indicator data...')
	merged = country_df.copy()
	for name, df in indicator_dfs.items():
		merged = pd.merge(merged, df[['Country Code', name]], left_on='Country ISO-3 Code', right_on='Country Code', how='left')
		merged = merged.drop(columns=['Country Code'])

	# 5. Handle missing values
	print('Handling missing values...')
	# Drop countries with all indicators missing
	indicator_cols = list(indicators.values())
	merged = merged.dropna(subset=indicator_cols, how='all')
	# Impute missing values with column mean
	for col in indicator_cols:
		merged[col] = merged[col].fillna(merged[col].mean())

	# 6. Save to CSV
	merged.to_csv('relocation_data.csv', index=False)
	print('Saved cleaned data to relocation_data.csv')

if __name__ == '__main__':
	main()
