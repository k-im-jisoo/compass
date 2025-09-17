import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('relocation_data_normalized.csv')
    return df

def get_indicator_columns(df):
    # Normalized columns end with _Norm
    return [col for col in df.columns if col.endswith('_Norm')]

def main():
    st.title('Compass: International Relocation Dashboard')
    df = load_data()
    indicator_cols = get_indicator_columns(df)
    indicator_labels = [col.replace('_Norm', '') for col in indicator_cols]
    # Sidebar filters
    regions = sorted(df['Region'].unique())
    selected_regions = st.sidebar.multiselect('Filter by Region', regions, default=regions)
    filtered_df = df[df['Region'].isin(selected_regions)]
    countries = filtered_df['Country Name'].unique()
    selected_countries = st.sidebar.multiselect('Select up to 5 Countries', countries, default=countries[:5], max_selections=5)
    if not selected_countries:
        st.warning('Please select at least one country.')
        return
    compare_df = filtered_df[filtered_df['Country Name'].isin(selected_countries)]
    # Radar chart
    st.header('Country Comparison: Radar Chart')
    radar_fig = go.Figure()
    for _, row in compare_df.iterrows():
        radar_fig.add_trace(go.Scatterpolar(
            r=row[indicator_cols].values,
            theta=indicator_labels,
            fill='toself',
            name=row['Country Name']
        ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True
    )
    st.plotly_chart(radar_fig, use_container_width=True)
    # Bar charts for each indicator
    st.header('Indicator Bar Charts')
    indicator_explanations = {
        'Hospital Beds': 'Number of hospital beds per 1,000 people. Higher is better.',
        'Air Pollution': 'Mean annual exposure to PM2.5 air pollution (micrograms per cubic meter). Lower is better.',
        'Secondary School Enrollment': 'Percentage of relevant age group enrolled in secondary school. Higher is better.',
        'Disease Mortality': 'Deaths from communicable diseases (% of total deaths). Lower is better.',
        'Traffic Deaths': 'Estimated road traffic deaths per 100,000 people. Lower is better.'
    }
    for norm_col, label in zip(indicator_cols, indicator_labels):
        orig_col = label  # original column name
        st.subheader(label)
        st.markdown(f"**{indicator_explanations.get(label, '')}**")
        if orig_col in compare_df.columns:
            bar_fig = px.bar(compare_df, x='Country Name', y=orig_col, color='Country Name', labels={orig_col: f'{label} (Original Value)'})
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info(f'Original data for {label} not found.')

if __name__ == '__main__':
    main()
