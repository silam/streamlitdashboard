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

    st.divider()
    st.header("Filters")

    min_date, max_date = pd.to_datetime(df["date"]).min(), pd.to_datetime(df["date"]).max()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    sel_regions = st.multiselect("Region", sorted(df["region"].unique()), default=sorted(df["region"].unique()))
    sel_channels = st.multiselect("Channel", sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
    sel_categories = st.multiselect("Category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))

    min_rating = st.slider("Minimum survey rating", 1, 5, 1)

                                                                                                
st.divider()
with st.expander("What-If: Discount Impact"):
    with st.form("whatif_form"):
        base_price = st.number_input("Average price", min_value=1.0, value=float(df.price.mean()), step=1.0)
        current_discount = st.slider("Current discount %", 0, 80, 10)
        proposed_discount = st.slider("Proposed discount %", 0, 80, 20)
        price_elasticity = st.slider("Elasticity (units per 10% discount)", 0.0, 2.0, 0.6, 0.1)
        submitted = st.form_submit_button("Estimate Impact")
    if submitted:
        cur_units = df["units"].mean()
        delta_disc = (proposed_discount - current_discount) / 10.0
        projected_units = max(0, cur_units * (1 + price_elasticity * delta_disc))
        cur_price = base_price * (1 - current_discount / 100)
        new_price = base_price * (1 - proposed_discount / 100)
        st.metric("Projected Units", f"{projected_units:,.0f}", delta=f"{projected_units - cur_units:,.0f}")
        st.metric("Projected Revenue", f"${new_rev:,.0f}", delta=f"${new_rev - cur_rev:,.0f}")

mask = (
    (pd.to_datetime(df["date"]).between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
    (df["region"].isin(sel_regions)) &
    (df["channel"].isin(sel_channels)) &
    (df["category"].isin(sel_categories)) &
    (df["survey_rating"] >= min_rating)
)
filtered = df.loc[mask].copy()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Revenue", f"${filtered['sales'].sum():,.0f}")
with col2:
    st.metric("Units", f"{filtered['units'].sum():,.0f}")
with col3:
    aov = (filtered['sales'].sum() / filtered['units'].sum()) if filtered['units'].sum() > 0 else 0
    
    st.metric("AOV", f"${aov:,.2f}")
with col4:
    st.metric("Avg Survey", f"{filtered['survey_rating'].mean():.2f} / 5")

st.divider()
ts = filtered.groupby('date', as_index=False).agg(revenue=('sales', 'sum'), units=('units', 'sum'), rating=('survey_ra...
(...).mark_line().encode(x='date:T', y='revenue:Q', tooltip=['date:T', 'revenue:Q', 'units:Q', 'rat...
st.altair_chart(line_rev, use_container_width=True)

cat = filtered.groupby('category', as_index=False).agg(revenue=('sales', 'sum'), units=('units', 'sum'))
bar_cat = alt.Chart(cat).mark_bar().encode(x='category:N', y='revenue:Q', tooltip=['category', 'revenue', 'units']).pr...

reg = filtered.groupby('region', as_index=False).agg(revenue=('sales', 'sum'), units=('units', 'sum'))
bar_reg = alt.Chart(reg).mark_bar().encode(x='region:N', y='revenue:Q', tooltip=['region', 'revenue', 'units']).proper...

c1, c2 = st.columns(2)
with c1:
    st.altair_chart(bar_cat, use_container_width=True)
with c2:
    st.altair_chart(bar_reg, use_container_width=True)

hist = alt.Chart(filtered).mark_bar().encode(x=alt.X('survey_rating:Q', bin=alt.Bin(maxbins=5)), y='count()', tooltip=...
st.altair_chart(hist, use_container_width=True)

corr = alt.Chart(ts).mark_circle(size=80).encode(x='rating:Q', y='revenue:Q', tooltip=['date:T', 'rating:Q', 'revenue:...
st.altair_chart(corr, use_container_width=True)

st.divider()

st.subheader("Filtered Data")
st.dataframe(filtered, use_container_width=True)

csv_buf = StringIO()
filtered.to_csv(csv_buf, index=False)
st.download_button("Download filtered CSV", data=csv_buf.getvalue(), file_name="filtered_sales.csv", mime="text/csv")
st.caption("Use the sidebar to adjust filters or upload your own dataset.")

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