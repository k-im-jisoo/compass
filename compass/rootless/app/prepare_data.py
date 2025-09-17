import pandas as pd
import pycountry

# Define a mapping from country to region (World Bank style)
# For simplicity, use pycountry_convert if available, else fallback to a static mapping
try:
    import pycountry_convert as pc
    def get_region(country_code):
        try:
            continent_code = pc.country_alpha3_to_continent_code(country_code)
            return pc.convert_continent_code_to_continent_name(continent_code)
        except Exception:
            return 'Other'
except ImportError:
    # Fallback: minimal static mapping for demonstration
    def get_region(country_code):
        # Add more mappings as needed
        region_map = {
            'USA': 'North America', 'CAN': 'North America', 'MEX': 'North America',
            'FRA': 'Europe', 'DEU': 'Europe', 'GBR': 'Europe',
            'CHN': 'Asia', 'JPN': 'Asia', 'KOR': 'Asia',
            'AUS': 'Oceania', 'NZL': 'Oceania',
            'BRA': 'South America', 'ARG': 'South America',
            'ZAF': 'Africa', 'EGY': 'Africa',
        }
        return region_map.get(country_code, 'Other')

def normalize_columns(df, indicator_cols):
    # Min-Max normalization to [0, 1]
    norm_df = df.copy()
    # Indicators to invert (higher is worse)
    invert_cols = ['Air Pollution', 'Disease Mortality', 'Traffic Deaths']
    for col in indicator_cols:
        min_val = norm_df[col].min()
        max_val = norm_df[col].max()
        if max_val > min_val:
            normed = (norm_df[col] - min_val) / (max_val - min_val)
        else:
            normed = 0.0
        # Invert if needed
        if col in invert_cols:
            normed = 1 - normed
        norm_df[col + '_Norm'] = normed
    return norm_df

def main():
    import os
    # Always use the project root for relocation_data.csv
    import pathlib
    project_root = pathlib.Path(__file__).parent.parent.parent
    csv_path = project_root / 'relocation_data.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f'relocation_data.csv not found at {csv_path}')
    df = pd.read_csv(csv_path)
    indicator_cols = [col for col in df.columns if col not in ['Country Name', 'Country ISO-3 Code', 'Region']]
    # Add region column
    df['Region'] = df['Country ISO-3 Code'].apply(get_region)
    # Normalize indicator columns
    norm_df = normalize_columns(df, indicator_cols)
    # Save for Streamlit app
    norm_df.to_csv('relocation_data_normalized.csv', index=False)
    print('Saved relocation_data_normalized.csv with region and normalized indicators.')

if __name__ == '__main__':
    main()
