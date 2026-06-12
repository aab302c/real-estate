import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine

st.set_page_config(layout="wide", page_title="Аналитика Недвижимости СПб")
st.title("Рынок жилой недвижимости СПб")

# === ПОДКЛЮЧЕНИЕ К SUPABASE ===
SUPABASE_URL = "postgresql://postgres.mxkmpveociwhuyasdkyf:Vjnjhjkf_2024!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

def get_engine():
    return create_engine(SUPABASE_URL, connect_args={"sslmode": "require"})

@st.cache_data
def load_data():
    try:
        engine = get_engine()
        df = pd.read_sql("SELECT * FROM real_estate_spb", engine)
        
        if df.empty:
            st.error("❌ Таблица real_estate_spb пуста")
            return df
        
        # Приводим к числам, убираем битые строки
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["area"] = pd.to_numeric(df["area"], errors="coerce")
        df["reputation_score"] = pd.to_numeric(df["reputation_score"], errors="coerce")
        df.dropna(inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ Ошибка подключения к базе: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ---
    st.sidebar.header(" Фильтры")
    
    # Фильтр по району
    districts = ["Все"] + sorted(df["district"].unique().tolist())
    selected_district = st.sidebar.selectbox("Район", districts)

    # Фильтр по бюджету
    min_price_val, max_price_val = st.sidebar.slider(
        "Бюджет (млн ₽)", 
        int(df["price"].min()/1e6), 
        int(df["price"].max()/1e6), 
        (int(df["price"].min()/1e6), int(df["price"].max()/1e6))
    )

    # Фильтр по рейтингу
    min_rep = st.sidebar.slider("Мин. рейтинг репутации", 0, 100, 0)

    # Применение фильтров
    mask = (df["price"] >= min_price_val*1e6) & (df["price"] <= max_price_val*1e6) & (df["reputation_score"] >= min_rep)
    if selected_district != "Все":
        mask &= (df["district"] == selected_district)

    filtered_df = df[mask].copy()

    # Инициализация состояния выбора объекта
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None

    # Словарь для поиска ID по координатам
    coord_to_id = {
        (round(row["lat"], 4), round(row["lon"], 4)): row["id"] 
        for _, row in filtered_df.iterrows()
    }

    # --- ОСНОВНАЯ ОБЛАСТЬ: Карта | Карточка ---
    col_map, col_card = st.columns([2, 1])

    with col_map:
        st.subheader("🗺️ Карта объектов")
        
        m = folium.Map(location=[59.9343, 30.3351], zoom_start=11, tiles="OpenStreetMap")
        
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
                weight=2,
                tooltip=folium.Tooltip(tooltip_html, max_width=300),
                popup=None
            ).add_to(m)

        map_data = st_folium(m, width="100%", height=520, key="interactive_map")
        
        if map_data and map_data.get("last_object_clicked"):
            clicked = map_data["last_object_clicked"]
            lat = clicked.get("lat")
            lon = clicked.get("lng")
            
            if lat and lon:
                for coords, bid in coord_to_id.items():
                    if abs(coords[0] - lat) < 0.001 and abs(coords[1] - lon) < 0.001:
                        st.session_state.selected_id = bid
                        break

        if not filtered_df.empty:
            current_index = 0
            if st.session_state.selected_id and st.session_state.selected_id in filtered_df["id"].values:
                idx_series = filtered_df[filtered_df["id"] == st.session_state.selected_id].index
                if not idx_series.empty:
                    current_index = int(idx_series[0])
            
            selected_address = st.selectbox(
                "Или выберите объект из списка:", 
                options=filtered_df["address"],
                index=current_index,
                key="fallback_select"
            )
            
            if selected_address:
                new_id = filtered_df[filtered_df["address"] == selected_address]["id"].iloc[0]
                if new_id != st.session_state.selected_id:
                    st.session_state.selected_id = new_id

    with col_card:
        st.subheader("📋 Карточка предложения")
        
        if st.session_state.selected_id is not None:
            prop = filtered_df[filtered_df["id"] == st.session_state.selected_id]
            
            if not prop.empty:
                prop = prop.iloc[0]
                
                st.markdown(f"### 📍 {prop['address']}")
                st.info(f"{prop['rooms']}-комн. | 📐 {prop['area']} м² | {prop['floor']}/{prop['total_floors']} эт. | 💰 {prop['price']/1e6:.1f} млн ₽")
                st.divider()
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**🏗️ Общая информация**")
                    st.text(f"Серия: {prop['series']}")
                    st.text(f"Год постройки: {prop['year_built']}")
                    st.text(f"Стены: {prop['wall_type']}")
                    st.text(f"Лифт: {'✅' if prop['has_lift'] else '❌'} | Балкон: {'✅' if prop['has_balcony'] else '❌'}")
                with c2:
                    st.markdown("**🖼️ Фото**")
                    if prop["photo_url"]:
                        st.image(prop["photo_url"], use_container_width=True)
                    else:
                        st.caption("Фото недоступно")
                        
                st.divider()
                
                st.markdown("**🗣️ Отзывы о доме**")
                issues = [i.strip() for i in str(prop["top_issues"]).split(",") if i.strip()]
                if issues:
                    tags_html = "".join([
                        f'<span style="background:#e0e7ff; color:#1e3a8a; padding:4px 8px; border-radius:6px; margin:2px; display:inline-block; font-size:0.85em;">{tag}</span>' 
                        for tag in issues
                    ])
                    st.markdown(f"<div style='line-height:1.8;'>{tags_html}</div>", unsafe_allow_html=True)
                else:
                    st.text("Нет данных об отзывах")
                
                st.divider()
                
                st.markdown("**Инфраструктура (радиус 1 км)**")
                ic1, ic2, ic3, ic4 = st.columns(4)
                with ic1:
                    st.metric("🚇 До метро", f"{prop['dist_metro_m']} м")
                with ic2:
                    st.metric("🏫 Школы", prop["schools_1km"])
                with ic3:
                    st.metric("🌲 Парки", prop["parks_1km"])
                with ic4:
                    st.metric("🛍️ Магазины", prop["shops_1km"])
                
                st.divider()
                
                st.link_button("🔗 Открыть оригинальное объявление", prop["url"])
                
            else:
                st.warning("Объект не найден в текущей фильтрации.")
        else:
            st.info("👆 Нажмите на маркер на карте или выберите из списка, чтобы открыть карточку объекта.")

    st.caption("Прототип аналитической системы | СПбГЭТУ «ЛЭТИ» | 2026")
else:
    st.info("⏳ Ожидание данных из Supabase...")
