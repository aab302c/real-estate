import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine

st.set_page_config(layout="wide", page_title="Аналитика Недвижимости СПб")
st.title("Рынок жилой недвижимости СПб")

SUPABASE_URL = 'postgresql://postgres.mxkmpveociwhuyasdkyf:Vjnjhjkf_2024!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require'

@st.cache_data
def load_data():
    engine = create_engine(SUPABASE_URL)
    df = pd.read_sql("SELECT * FROM real_estate_spb", engine)
    
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["area"] = pd.to_numeric(df["area"], errors="coerce")
    df["reputation_score"] = pd.to_numeric(df["reputation_score"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    return df

df = load_data()

if df.empty:
    st.error("Нет данных с координатами")
    st.stop()

st.success(f"Загружено {len(df)} объектов")

col_map, col_card = st.columns([2, 1])

with col_map:
    m = folium.Map(location=[59.9343, 30.3351], zoom_start=11)
    
    for _, row in df.iterrows():
        color = "green" if row["reputation_score"] > 70 else "red"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            popup=f"{row['address']}<br>{row['price']//1000000} млн ₽",
            tooltip=row['address']
        ).add_to(m)
    
    st_folium(m, width="100%", height=500)

with col_card:
    st.info("Нажми на маркер")
