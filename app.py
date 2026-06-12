import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# === ПОДКЛЮЧЕНИЕ К SUPABASE ===
# Если используете .env файл
load_dotenv()

# Строка подключения (лучше хранить в .env, но для простоты можно указать явно)
SUPABASE_URL = "postgresql://postgres.mxkmpveociwhuyasdkyf:Vjnjhjkf_2024!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

def get_engine():
    """Создает движок SQLAlchemy с SSL для Supabase"""
    return create_engine(SUPABASE_URL, connect_args={"sslmode": "require"})

st.set_page_config(layout="wide", page_title="Аналитика Недвижимости СПб")
st.title("🏠 Рынок жилой недвижимости СПб")

@st.cache_data(ttl=300)  # Кеш на 5 минут
def load_data_from_db():
    """Загружает данные из таблицы real_estate_spb"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Загружаем все данные
            df = pd.read_sql("SELECT * FROM real_estate_spb", conn)
            
            # Приводим типы
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            df["area"] = pd.to_numeric(df["area"], errors="coerce")
            df["reputation_score"] = pd.to_numeric(df["reputation_score"], errors="coerce")
            df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
            df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
            
            # Удаляем строки без координат (не отобразятся на карте)
            df = df.dropna(subset=["lat", "lon"])
            
            return df
    except Exception as e:
        st.error(f"❌ Ошибка загрузки данных из базы: {e}")
        st.info("Убедитесь, что таблица real_estate_spb существует и содержит данные")
        return pd.DataFrame()

# === ЗАГРУЗКА ДАННЫХ ===
df = load_data_from_db()

if not df.empty:
    st.success(f"✅ Загружено {len(df)} объектов недвижимости")
    
    # --- БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ---
    st.sidebar.header("🔍 Фильтры")
    
    # Фильтр по району
    districts = ["Все"] + sorted(df["district"].dropna().unique().tolist())
    selected_district = st.sidebar.selectbox("Район", districts)
    
    # Фильтр по бюджету (в млн ₽)
    min_price_val, max_price_val = st.sidebar.slider(
        "Бюджет (млн ₽)", 
        float(df["price"].min() / 1e6), 
        float(df["price"].max() / 1e6), 
        (float(df["price"].min() / 1e6), float(df["price"].max() / 1e6)),
        step=0.5
    )
    
    # Фильтр по рейтингу
    min_rep = st.sidebar.slider("Мин. рейтинг репутации", 0, 100, 0)
    
    # Фильтр по количеству комнат
    rooms_options = ["Все", 1, 2, 3, 4]
    selected_rooms = st.sidebar.selectbox("Комнаты", rooms_options)
    
    # Применение фильтров
    mask = (
        (df["price"] >= min_price_val * 1e6) & 
        (df["price"] <= max_price_val * 1e6) & 
        (df["reputation_score"] >= min_rep)
    )
    
    if selected_district != "Все":
        mask &= (df["district"] == selected_district)
    
    if selected_rooms != "Все":
        mask &= (df["rooms"] == selected_rooms)
    
    filtered_df = df[mask].copy()
    
    st.sidebar.markdown("---")
    st.sidebar.metric("📊 Найдено объектов", len(filtered_df))
    
    # Инициализация состояния выбора объекта
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None
    
    # --- ОСНОВНАЯ ОБЛАСТЬ: Карта | Карточка ---
    col_map, col_card = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ Карта объектов")
        
        # Создаем карту с центром в СПб
        m = folium.Map(location=[59.9343, 30.3351], zoom_start=11, tiles="OpenStreetMap")
        
        # Добавляем маркеры на карту
        for _, row in filtered_df.iterrows():
            # Цвет маркера в зависимости от рейтинга
            if row["reputation_score"] and row["reputation_score"] > 70:
                color = "green"
            elif row["reputation_score"] and row["reputation_score"] > 50:
                color = "orange"
            else:
                color = "red"
            
            # HTML для Tooltip (при наведении)
            tooltip_html = f"""
            <div style="font-family: sans-serif; font-size: 13px;">
                <b>{row['address']}</b><br>
                💰 {int(row['price'] // 1_000_000)} млн ₽<br>
                🛏️ {int(row['rooms']) if row['rooms'] else '?'} комн. | 📐 {row['area']:.1f} м²<br>
                ⭐ Рейтинг: {int(row['reputation_score']) if row['reputation_score'] else '?'}
            </div>
            """
            
            # Создаем маркер
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=2,
                tooltip=folium.Tooltip(tooltip_html, max_width=300),
            ).add_to(m)
        
        # Отображаем карту
        map_data = st_folium(m, width="100%", height=520, key="interactive_map")
        
        # Обработка клика по карте
        if map_data and map_data.get("last_object_clicked"):
            clicked = map_data["last_object_clicked"]
            lat = clicked.get("lat")
            lon = clicked.get("lng")
            
            if lat and lon and not filtered_df.empty:
                # Поиск ближайшего объекта
                from math import sqrt
                min_dist = float('inf')
                nearest_idx = None
                for idx, row in filtered_df.iterrows():
                    dist = sqrt((row["lat"] - lat)**2 + (row["lon"] - lon)**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = idx
                if nearest_idx is not None:
                    st.session_state.selected_id = filtered_df.iloc[nearest_idx]["id"]
        
        # Выпадающий список для выбора объекта
        if not filtered_df.empty:
            # Создаем список адресов с ценами для отображения
            addresses_with_price = [
                f"{row['address'][:50]} - {int(row['price']//1_000_000)} млн ₽" 
                for _, row in filtered_df.iterrows()
            ]
            
            # Находим текущий индекс
            current_index = 0
            if st.session_state.selected_id is not None:
                idx_list = filtered_df[filtered_df["id"] == st.session_state.selected_id].index
                if len(idx_list) > 0:
                    current_index = filtered_df.index.get_loc(idx_list[0])
            
            selected_address = st.selectbox(
                "Или выберите объект из списка:", 
                options=addresses_with_price,
                index=current_index,
                key="fallback_select"
            )
            
            # Обновляем selected_id
            if selected_address:
                selected_idx = addresses_with_price.index(selected_address)
                new_id = filtered_df.iloc[selected_idx]["id"]
                if new_id != st.session_state.selected_id:
                    st.session_state.selected_id = new_id
    
    with col_card:
        st.subheader("📋 Карточка предложения")
        
        if st.session_state.selected_id is not None:
            prop = filtered_df[filtered_df["id"] == st.session_state.selected_id]
            
            if not prop.empty:
                prop = prop.iloc[0]
                
                # Краткое описание
                st.markdown(f"### 📍 {prop['address']}")
                
                # Основная информация в колонках
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Цена", f"{int(prop['price']//1_000_000)} млн ₽")
                with col2:
                    st.metric("🛏️ Комнаты", f"{int(prop['rooms'])}" if prop['rooms'] else "—")
                with col3:
                    st.metric("📐 Площадь", f"{prop['area']:.1f} м²" if prop['area'] else "—")
                
                st.divider()
                
                # Характеристики
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🏗️ Характеристики**")
                    st.write(f"📍 **Район:** {prop['district'] or '—'}")
                    st.write(f"🏢 **Этаж:** {int(prop['floor']) if prop['floor'] else '—'} / {int(prop['total_floors']) if prop['total_floors'] else '—'}")
                    st.write(f"🏛️ **Серия:** {prop['series'] or '—'}")
                    st.write(f"📅 **Год:** {int(prop['year_built']) if prop['year_built'] else '—'}")
                    st.write(f"🧱 **Стены:** {prop['wall_type'] or '—'}")
                
                with col2:
                    st.markdown("**🔧 Удобства**")
                    st.write(f"🔼 **Лифт:** {'✅ Да' if prop['has_lift'] else '❌ Нет'}")
                    st.write(f"🪟 **Балкон:** {'✅ Да' if prop['has_balcony'] else '❌ Нет'}")
                    st.write(f"⭐ **Рейтинг:** {int(prop['reputation_score']) if prop['reputation_score'] else '—'}")
                    st.write(f"🚇 **Метро:** {int(prop['dist_metro_m'])} м" if prop['dist_metro_m'] else "🚇 **Метро:** —")
                
                st.divider()
                
                # Отзывы и проблемы
                st.markdown("**🗣️ Отзывы и проблемы**")
                if prop['top_issues'] and prop['top_issues'] != 'нет данных':
                    issues = [i.strip() for i in str(prop['top_issues']).split(',') if i.strip()]
                    tags_html = "".join([
                        f'<span style="background:#e0e7ff; color:#1e3a8a; padding:4px 8px; border-radius:6px; margin:2px; display:inline-block; font-size:0.85em;">⚠️ {tag}</span>' 
                        for tag in issues
                    ])
                    st.markdown(f"<div style='line-height:1.8;'>{tags_html}</div>", unsafe_allow_html=True)
                else:
                    st.info("Нет данных о проблемах")
                
                st.divider()
                
                # Инфраструктура
                st.markdown("**🏪 Инфраструктура (радиус 1 км)**")
                ic1, ic2, ic3 = st.columns(3)
                with ic1:
                    st.metric("🏫 Школы", int(prop['schools_1km']) if prop['schools_1km'] else "—")
                with ic2:
                    st.metric("🌲 Парки", int(prop['parks_1km']) if prop['parks_1km'] else "—")
                with ic3:
                    st.metric("🛍️ Магазины", int(prop['shops_1km']) if prop['shops_1km'] else "—")
                
                # Фото (если есть)
                if prop['photo_url'] and prop['photo_url'] != 'None' and pd.notna(prop['photo_url']):
                    st.divider()
                    st.markdown("**🖼️ Фото объекта**")
                    st.image(prop['photo_url'], use_container_width=True)
                
                # Ссылка на объявление
                if prop['url'] and prop['url'] != 'None' and pd.notna(prop['url']):
                    st.divider()
                    st.link_button("🔗 Открыть оригинальное объявление", prop['url'])
            else:
                st.warning("Объект не найден в текущей фильтрации.")
        else:
            st.info("👆 Нажмите на маркер на карте или выберите объект из списка")
    
    st.caption("Прототип аналитической системы | Данные из Supabase | 2026")
    
    # Кнопка обновления данных в сайдбаре
    if st.sidebar.button("🔄 Обновить данные"):
        st.cache_data.clear()
        st.rerun()
        
else:
    st.info("⏳ Нет данных в таблице real_estate_spb. Добавьте объекты через парсер или вручную.")
    
    # Инструкция по добавлению данных
    with st.expander("📝 Как добавить данные?"):
        st.markdown("""
        ### Варианты:
        1. **Запустить парсер** - собирает данные с Cian.ru
        2. **Добавить вручную** через SQL запрос:
        ```sql
        INSERT INTO real_estate_spb (id, address, lat, lon, price, area, rooms, ...)
        VALUES (...);
