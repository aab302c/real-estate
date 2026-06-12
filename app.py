import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine
import math

# === ПОДКЛЮЧЕНИЕ К SUPABASE ===
SUPABASE_URL = "postgresql://postgres.mxkmpveociwhuyasdkyf:Vjnjhjkf_2024!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def get_engine():
    return create_engine(SUPABASE_URL, connect_args={"sslmode": "require"})

st.set_page_config(layout="wide", page_title="Аналитика Недвижимости СПб")
st.title("Рынок жилой недвижимости СПб")

@st.cache_data(ttl=300)
def load_data():
    try:
        engine = get_engine()
        df = pd.read_sql("SELECT * FROM real_estate_spb", engine)
        
        if df.empty:
            return df
            
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["area"] = pd.to_numeric(df["area"], errors="coerce")
        df["reputation_score"] = pd.to_numeric(df["reputation_score"], errors="coerce")
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        
        df = df.dropna(subset=["lat", "lon"])
        return df
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Нет данных. Добавьте объекты в таблицу real_estate_spb")
    st.stop()

st.success(f"Загружено {len(df)} объектов")

# --- ФИЛЬТРЫ ---
st.sidebar.header("Фильтры")

districts = ["Все"] + sorted(df["district"].dropna().unique().tolist())
selected_district = st.sidebar.selectbox("Район", districts)

min_price = float(df["price"].min() / 1e6)
max_price = float(df["price"].max() / 1e6)
price_range = st.sidebar.slider("Бюджет (млн ₽)", min_price, max_price, (min_price, max_price))

min_rating = st.sidebar.slider("Мин. рейтинг", 0, 100, 0)

rooms_list = ["Все"] + sorted(df["rooms"].dropna().unique().tolist())
selected_rooms = st.sidebar.selectbox("Комнаты", rooms_list)

# Применяем фильтры
mask = (df["price"] >= price_range[0] * 1e6) & (df["price"] <= price_range[1] * 1e6)
mask &= (df["reputation_score"] >= min_rating)

if selected_district != "Все":
    mask &= (df["district"] == selected_district)
if selected_rooms != "Все":
    mask &= (df["rooms"] == selected_rooms)

filtered_df = df[mask].copy()
st.sidebar.metric("Найдено", len(filtered_df))

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# --- КАРТА И КАРТОЧКА ---
col_map, col_card = st.columns([2, 1])

with col_map:
    st.subheader("Карта объектов")
    
    m = folium.Map(location=[59.9343, 30.3351], zoom_start=11)
    
    for _, row in filtered_df.iterrows():
        if row["reputation_score"] > 70:
            color = "green"
        elif row["reputation_score"] > 50:
            color = "orange"
        else:
            color = "red"
        
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"{row['address']}<br>{row['price']//1000000} млн ₽<br>{row['rooms']} комн., {row['area']} м²",
            tooltip=row['address']
        ).add_to(m)
    
    map_data = st_folium(m, width="100%", height=500)
    
    if map_data and map_data.get("last_object_clicked"):
        lat = map_data["last_object_clicked"]["lat"]
        lng = map_data["last_object_clicked"]["lng"]
        
        # Ищем ближайший объект
        min_dist = float("inf")
        nearest_id = None
        for _, row in filtered_df.iterrows():
            dist = math.hypot(row["lat"] - lat, row["lon"] - lng)
            if dist < min_dist:
                min_dist = dist
                nearest_id = row["id"]
        if nearest_id:
            st.session_state.selected_id = nearest_id
    
    if not filtered_df.empty:
        options = [f"{row['address'][:40]} - {row['price']//1000000} млн" for _, row in filtered_df.iterrows()]
        idx = 0
        if st.session_state.selected_id:
            ids = filtered_df["id"].tolist()
            if st.session_state.selected_id in ids:
                idx = ids.index(st.session_state.selected_id)
        
        selected = st.selectbox("Выберите объект", options, index=idx)
        if selected:
            st.session_state.selected_id = filtered_df.iloc[options.index(selected)]["id"]

with col_card:
    st.subheader("Карточка объекта")
    
    if st.session_state.selected_id:
        prop = filtered_df[filtered_df["id"] == st.session_state.selected_id]
        if not prop.empty:
            p = prop.iloc[0]
            
            st.markdown(f"**{p['address']}**")
            st.metric("Цена", f"{p['price']//1000000} млн ₽")
            
            c1, c2 = st.columns(2)
            c1.metric("Комнаты", p['rooms'] if p['rooms'] else "-")
            c2.metric("Площадь", f"{p['area']:.1f} м²" if p['area'] else "-")
            
            c1, c2 = st.columns(2)
            c1.metric("Этаж", f"{p['floor']}/{p['total_floors']}" if p['floor'] else "-")
            c2.metric("Рейтинг", p['reputation_score'] if p['reputation_score'] else "-")
            
            st.write(f"**Район:** {p['district'] or '-'}")
            st.write(f"**Год постройки:** {p['year_built'] or '-'}")
            st.write(f"**Серия:** {p['series'] or '-'}")
            st.write(f"**Метро:** {p['dist_metro_m']} м" if p['dist_metro_m'] else "Метро: -")
            
            if p['photo_url'] and str(p['photo_url']) != 'nan':
                st.image(p['photo_url'], use_container_width=True)
            
            if p['url'] and str(p['url']) != 'nan':
                st.link_button("Открыть объявление", p['url'])
        else:
            st.info("Выберите объект на карте")
    else:
        st.info("Нажмите на маркер на карте")
