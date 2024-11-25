import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

CITY_KEY = 'NAME_HE'
DATE_KEY = 'date'
TIME_KEY = 'time'
DATETIME_KEY = 'alertDate'

# Check if running in Streamlit context
if not get_script_run_ctx():
    st.error("This script must be run using the `streamlit run` command.")
    sys.exit()


# Load the data
def load_data(city_name: str):
    file_path = os.path.join('cities', f'{city_name}.csv')
    df = pd.read_csv(file_path)
    # Convert 'datetime' to datetime format if not already
    df[DATE_KEY] = pd.to_datetime(df[DATE_KEY], dayfirst=True)
    df['hour'] = pd.to_datetime(df[DATETIME_KEY]).dt.hour
    return df


# Streamlit App
st.title("ניהול סיכונים לתא המשפחתי - אזעקות")

# Input 1: City Picker
with open('cities.txt', 'r', encoding='utf-8') as file:
    city_names = file.readlines()  # Read all lines into a list

# Strip newline characters and extra spaces
city_names = [city.strip() for city in city_names]
selected_city = st.selectbox("Select a City", city_names)

# Load data once to optimize performance
df = load_data(city_name=selected_city)

# Input 2: Date & Time Picker
start_date = st.date_input("Select Start Date", value=pd.to_datetime('2024-10-01'))
end_date = st.date_input("Select End Date", value=pd.to_datetime('2024-11-24'))

# Input 3: Planned hour
selected_time = st.time_input("Select a time:", value="now", step=60*60)

# Filter the DataFrame by date range and city
filtered_df = df[
    (df[DATE_KEY] >= pd.to_datetime(start_date)) &
    (df[DATE_KEY] <= pd.to_datetime(end_date)) &
    (df[CITY_KEY] == selected_city)
]

# Output 1: Counter of alerts
if not filtered_df.empty:
    alert_count = filtered_df[CITY_KEY].count()
    st.metric(label=f"Total Alerts in {selected_city}", value=alert_count)
else:
    st.metric(label=f"Total Alerts in {selected_city}", value=0)

# Output 2: Histogram by Alerts Over Time
if not filtered_df.empty:
    st.write("### Alerts Over Time")
    grouped_data = filtered_df.groupby(DATE_KEY).size().reset_index(name='count')
    fig = px.bar(
        grouped_data,
        x=DATE_KEY,
        y='count',
        labels={DATE_KEY: 'Date', 'count': 'Number of Alerts'},
        title=f"Alerts Histogram for {selected_city}"
    )
    fig.update_layout(
        title=dict(x=0.35),
    )
    st.plotly_chart(fig)
else:
    st.write("No alerts found for the selected filters.")

# Output 3: Histogram by Hour of Day
if not filtered_df.empty:
    st.write("### Alerts by Hour of the Day")
    hourly_data = filtered_df.groupby('hour').size().reset_index(name='count')
    fig_hourly = px.bar(
        hourly_data,
        x='hour',
        y='count',
        labels={'hour': 'Hour of the Day', 'count': 'Number of Alerts'},
        title=f"Hourly Distribution of Alerts in {selected_city}",
        text_auto=True
    )
    fig_hourly.update_layout(
        xaxis=dict(tickmode='linear'),
        title=dict(x=0.3),
    )  # Ensure all hours are shown
    st.plotly_chart(fig_hourly)
else:
    st.write("No hourly data found for the selected filters.")
    hourly_data = None

# Output 4: The probability to alert at the selected time
difference_in_days = (end_date - start_date).days
divider = difference_in_days * 24 * 6
hourly_df = df.groupby(DATETIME_KEY).size().reset_index(name='count')
hourly_df['alertDate'] = pd.to_datetime(hourly_df['alertDate'])
hourly_df['hour'] = hourly_df['alertDate'].dt.hour

if len(hourly_df) > 0:
    print("Yes")
    print(selected_time.hour)
    print(hourly_df[DATETIME_KEY].dt.hour)
    if divider > 0:
        probability = hourly_df[hourly_df['hour'] == selected_time.hour]['alertDate'].count() / divider
    else:
        probability = 0
else:
    print("No")
    print(selected_time.hour)
    probability = 0

probability_in_percent = probability * 100


st.write(f"### The probability [%] to alert at {selected_time} in {selected_city}")
st.metric(
    value=probability_in_percent,
    label="Probability in %"
)

