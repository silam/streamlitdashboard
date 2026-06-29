import streamlit as st
import pandas as pd
import numpy as np
import altair as alt #declarative statistical visualization library for Python
from io import StringIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Retail and Survey Dashboard" , 
                   page_icon="",
                   layout="wide")

st.title("Retail Sales and Survey InsightsDashboard")

st.caption("Filter , explore and run quick what-if analysis on retail sales and survey data")
@st.cache_data
def generate_sample_data(rows: int = 1000, start_date: str = None):
    if start_date is None:
        start = datetime.today() - timedelta(days=180)
    else:
        start = pd.to_datetime(start_date)

    dates = pd.date_range(start, periods=180)

    regions = ['North', 'South', 'East', 'West']
    channels = ['Store', 'Online']
    categories = ['Electronics', 'Clothing', 'Apparel', 'Home', 'Grocery']
    products = {
        "Electronics": ['Phone', 'Laptop', 'Camera', 'Headphones'],
        "Apparel": ['T-Shirt', 'Jeans', 'Jackets', 'Jacket'],
        "Home": ['Lamps', 'Chair', 'Table' , 'Curtains'],
        "Grocery": ['Cereal', 'Coffee', 'Pasta', 'Snacks']
    }

    rng = np.random.default_rng(seed=42)
    data = []
    for _ in range(rows):
        d = rng.choice(dates)
        region = rng.choice(regions)
        channel = rng.choice(channels)
        category = rng.choice(categories)
        product = rng.choice(products[category])
        price = float(np.round(rng.uniform(5, 500), 2))
        discount_pct = float(np.round(rng.uniform(0, 0.4), 2))
        base_units = rng.integers(1, 15)
        d_ts = pd.Timestamp(d)
        seasonal = 1 + 0.3 * np.sin((d_ts.dayofyear / 365) * 2 * np.pi)
        promo_boost = 1 + (0.5 * discount_pct)
        units = max(1, int(np.round(base_units * seasonal * promo_boost + rng.normal(0, 2))))
        sales = float(np.round(price * (1 - discount_pct) * units, 2))
        survey_rating = int(np.clip(rng.normal(3.8, 0.9), 1, 5).round())
        nps = int(np.clip(rng.normal(20, 25), -100, 100))

        data.append([d, region, channel, category, product, price, discount_pct, units, sales, survey_rating, nps])

    df = pd.DataFrame(data, columns=['Date', 'Region', 'Channel', 'Category', 'Product', 'Price', 'Discount_Pct', 'Units_Sold', 'Sales_Amount', 'Survey_Rating', 'NPS'])
    
    df["date"] = pd.to_datetime(df["Date"]).dt.date

    return df

def coerce_schema(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    required  = ['Date', 'Region', 'Channel', 'Category', 'Product', 'Price', 'Discount_Pct', 'Units', 'Sales', 'Survey_Rating', 'NPS']
    missing = required - set(df.columns)

    for col in missing:
        st.warning(f"Column '{col}' is missing in the uploaded data. Filling with default values.")

        if col in {'region', 'channel', 'category', 'product'}:
            df[col] = "Unknown"
        elif col in ['Price', 'Discount_Pct', 'Sales']:
            df[col] = 0.0
        elif col in ['Units', 'Survey_Rating', 'NPS']:
            df[col] = 0
        elif col == 'Date':
            df[col] = pd.to_datetime('today').date()
        else:
            df[col] = ""
   
    return df

with st.sidebar:
    st.header("Data Upload and Filters")
    uploaded_file = st.file_uploader("Upload your retail sales and survey data (CSV format)", type=["csv"])
    if uploaded_file is not None:
        try:
            raw = pd.read_csv(uploaded_file)
            df = coerce_schema(raw.copy())
            st.success("Data uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading the uploaded file: {e}")
            df = generate_sample_data()
    else:
        st.info("No file uploaded. Using sample data.")
        df = generate_sample_data(rows=1500)
        st.info("Sample data generated with 1500 rows.")

#     st.divider()
#     st.header("Filters")


    # Date filter
    # min_date = df['Date'].min()
    # max_date = df['Date'].max()
    # date_range = st.date_input("Select date range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # # Region filter
    # regions = df['Region'].unique().tolist()
    # selected_regions = st.multiselect("Select regions", regions, default=regions)

    # # Channel filter
    # channels = df['Channel'].unique().tolist()
    # selected_channels = st.multiselect("Select channels", channels, default=channels)

    # # Category filter
    # categories = df['Category'].unique().tolist()
    # selected_categories = st.multiselect("Select categories", categories, default=categories)