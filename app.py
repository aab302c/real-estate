import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine
import math

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

# --- ФИЛЬТРЫ В БОКОВОЙ ПАНЕЛИ ---
st.sidebar.header("Фильтры")

districts = ["Все"] + sorted(df["district"].dropna().unique().tolist())
selected_district = st.sidebar.selectbox("Район", districts)

# Фикс для случая, когда одна цена
min_price = int(df["price"].min()/1e6)
max_price = int(df["price"].max()/1e6)

if min_price == max_price:
    price_range = st.sidebar.slider("Бюджет (млн ₽)", min_price, max_price + 1, (min_price, max_price + 1))
else:
    price_range = st.sidebar.slider("Бюджет (млн ₽)", min_price, max_price, (min_price, max_price))

min_rep = st.sidebar.slider("Мин. рейтинг", 0, 100, 0)

# Применяем фильтры
mask = (df["price"] >= price_range[0]*1e6) & (df["price"] <= price_range[1]*1e6) & (df["reputation_score"] >= min_rep)
if selected_district != "Все":
    mask &= (df["district"] == selected_district)

filtered_df = df[mask].copy()

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# --- КАРТА И КАРТОЧКА ---
col_map, col_card = st.columns([2, 1])

with col_map:
    st.subheader("Карта объектов")
    
    m = folium.Map(location=[59.9343, 30.3351], zoom_start=11)
    
    for _, row in filtered_df.iterrows():
        color = "green" if row["reputation_score"] > 70 else "red"
        
        tooltip_html = f"""
        <div style="font-family: sans-serif; font-size: 13px;">
            <b>{row['address']}</b><br>
            💰 {row['price'] // 1_000_000} млн ₽<br>
            🛏️ {row['rooms']} комн. | 📐 {row['area']} м²<br>
            ⭐ Рейтинг: {row['reputation_score']}
        </div>
        """
        
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_html, max_width=300),
            popup=None
        ).add_to(m)
    
    map_data = st_folium(m, width="100%", height=500, key="map")
    
    # Обработка клика по карте
    if map_data and map_data.get("last_object_clicked"):
        lat = map_data["last_object_clicked"]["lat"]
        lng = map_data["last_object_clicked"]["lng"]
        
        min_dist = float("inf")
        for _, row in filtered_df.iterrows():
            dist = math.hypot(row["lat"] - lat, row["lon"] - lng)
            if dist < min_dist:
                min_dist = dist
                st.session_state.selected_id = row["id"]
    
    # Выпадающий список
    if not filtered_df.empty:
        addresses = filtered_df["address"].tolist()
        current_index = 0
        if st.session_state.selected_id:
            ids = filtered_df["id"].tolist()
            if st.session_state.selected_id in ids:
                current_index = ids.index(st.session_state.selected_id)
        
        selected_address = st.selectbox("Или выберите из списка:", addresses, index=current_index)
        if selected_address:
            st.session_state.selected_id = filtered_df[filtered_df["address"] == selected_address]["id"].iloc[0]

with col_card:
    st.subheader("Карточка предложения")
    
    if st.session_state.selected_id:
        prop = filtered_df[filtered_df["id"] == st.session_state.selected_id]
        if not prop.empty:
            prop = prop.iloc[0]
            
            st.markdown(f"### 📍 {prop['address']}")
            st.info(f"{prop['rooms']}-комн. | 📐 {prop['area']} м² | 💰 {prop['price']/1e6:.1f} млн ₽")
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🏗️ Общая информация**")
                st.write(f"Район: {prop['district'] or '-'}")
                st.write(f"Этаж: {prop['floor']}/{prop['total_floors']}" if prop['floor'] else "Этаж: -")
                st.write(f"Год: {prop['year_built'] or '-'}")
                st.write(f"Серия: {prop['series'] or '-'}")
                st.write(f"Стены: {prop['wall_type'] or '-'}")
                st.write(f"Лифт: {'✅' if prop['has_lift'] else '❌'}")
            
            with col2:
                st.markdown("**🏪 Инфраструктура**")
                st.write(f"🚇 Метро: {prop['dist_metro_m']} м" if prop['dist_metro_m'] else "Метро: -")
                st.write(f"🏫 Школы: {prop['schools_1km'] or '-'}")
                st.write(f"🌲 Парки: {prop['parks_1km'] or '-'}")
                st.write(f"🛍️ Магазины: {prop['shops_1km'] or '-'}")
            
            st.divider()
            
            st.markdown("**🗣️ Отзывы**")
            if prop['top_issues']:
                st.write(prop['top_issues'])
            else:
                st.write("Нет данных")
            
            if prop['photo_url']:
                st.image(prop['photo_url'], use_container_width=True)
            
            if prop['url']:
                st.link_button("Открыть объявление", prop['url'])
        else:
            st.info("Выберите объект")
    else:
        st.info("👆 Нажмите на маркер")

st.caption("2026")
