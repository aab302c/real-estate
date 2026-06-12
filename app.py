import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine

st.set_page_config(layout="wide", page_title="Аналитика Недвижимости СПб")
st.title("Рынок жилой недвижимости СПб")

SUPABASE_URL = 'postgresql://postgres.mxkmpveociwhuyasdkyf:Vjnjhjkf_2024!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require'

# === АДМИН-ПАНЕЛЬ ДЛЯ ДОБАВЛЕНИЯ ДАННЫХ ===
with st.expander("🔧 Админ-панель (добавить тестовые данные)"):
    if st.button("➕ Добавить тестовый объект"):
        try:
            engine = create_engine(SUPABASE_URL)
            with engine.connect() as conn:
                conn.execute(
                    "INSERT INTO real_estate_spb (id, address, lat, lon, price, area, rooms, reputation_score, floor, total_floors, series, year_built, wall_type, has_lift, has_balcony, district, dist_metro_m) VALUES (1, 'Невский проспект, 1', 59.9343, 30.3351, 15000000, 65.5, 3, 75, 5, 9, 'Сталинка', 1955, 'Кирпич', true, true, 'Центральный', 500) ON CONFLICT (id) DO NOTHING"
                )
                conn.commit()
            st.success("✅ Тестовый объект добавлен! Обнови страницу (F5)")
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка: {e}")

@st.cache_data
def load_data():
    try:
        engine = create_engine(SUPABASE_URL)
        df = pd.read_sql("SELECT * FROM real_estate_spb", engine)
        
        if df.empty:
            return df
        
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["area"] = pd.to_numeric(df["area"], errors="coerce")
        df["reputation_score"] = pd.to_numeric(df["reputation_score"], errors="coerce")
        df.dropna(inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.success(f"✅ Загружено {len(df)} объектов")
    
    st.sidebar.header("Фильтры")
    
    districts = ["Все"] + sorted(df["district"].dropna().unique().tolist())
    selected_district = st.sidebar.selectbox("Район", districts)

    min_price_val, max_price_val = st.sidebar.slider(
        "Бюджет (млн ₽)", 
        int(df["price"].min()/1e6), 
        int(df["price"].max()/1e6), 
        (int(df["price"].min()/1e6), int(df["price"].max()/1e6))
    )

    min_rep = st.sidebar.slider("Мин. рейтинг репутации", 0, 100, 0)

    mask = (df["price"] >= min_price_val*1e6) & (df["price"] <= max_price_val*1e6) & (df["reputation_score"] >= min_rep)
    if selected_district != "Все":
        mask &= (df["district"] == selected_district)

    filtered_df = df[mask].copy()

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None

    col_map, col_card = st.columns([2, 1])

    with col_map:
        st.subheader("Карта объектов")
        
        m = folium.Map(location=[59.9343, 30.3351], zoom_start=11)
        
        for _, row in filtered_df.iterrows():
            color = "green" if row["reputation_score"] > 70 else "red"
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=f"{row['address']}<br>{row['price']//1000000} млн ₽",
                tooltip=row['address']
            ).add_to(m)
        
        map_data = st_folium(m, width="100%", height=500)
        
        if map_data and map_data.get("last_object_clicked"):
            lat = map_data["last_object_clicked"]["lat"]
            lng = map_data["last_object_clicked"]["lng"]
            
            min_dist = float("inf")
            for _, row in filtered_df.iterrows():
                dist = ((row["lat"] - lat)**2 + (row["lon"] - lng)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    st.session_state.selected_id = row["id"]

    with col_card:
        st.subheader("Карточка предложения")
        
        if st.session_state.selected_id is not None:
            prop = filtered_df[filtered_df["id"] == st.session_state.selected_id]
            if not prop.empty:
                prop = prop.iloc[0]
                st.markdown(f"### 📍 {prop['address']}")
                st.metric("💰 Цена", f"{prop['price']//1000000} млн ₽")
                st.write(f"🛏️ Комнаты: {prop['rooms']}")
                st.write(f"📐 Площадь: {prop['area']} м²")
                st.write(f"📍 Район: {prop['district']}")
                if prop['year_built']:
                    st.write(f"📅 Год постройки: {prop['year_built']}")
            else:
                st.warning("Объект не найден")
        else:
            st.info("👆 Нажмите на маркер на карте")

    st.caption("Прототип аналитической системы | СПбГЭТУ «ЛЭТИ» | 2026")
else:
    st.info("Нет данных. Нажми кнопку выше, чтобы добавить тестовый объект")
