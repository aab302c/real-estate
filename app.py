import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Рынок жилой недвижимости СПб",
    page_icon="🏠",
    layout="wide"
)

# === ДАННЫЕ ===
buildings_data = [
    {
        "id": 1,
        "name": "наб. реки Фонтанки, д. 45",
        "address": "наб. реки Фонтанки, д. 45",
        "lat": 59.9343,
        "lon": 30.3351,
        "rooms": 2,
        "area": 65.0,
        "floor": 4,
        "total_floors": 9,
        "price": 18.5,
        "series": "137 серия",
        "year_built": 1985,
        "wall_type": "Кирпич",
        "has_lift": False,
        "has_balcony": False,
        "photo_url": None,
        "top_issues": ["Шумоизоляция", "Старый лифт", "Чистый подъезд"],
        "dist_metro_m": 350,
        "schools_1km": 4,
        "parks_1km": 2,
        "shops_1km": 12,
        "reputation_score": 85
    },
    {
        "id": 2,
        "name": "Невский пр., д. 100",
        "address": "Невский пр., д. 100",
        "lat": 59.9311,
        "lon": 30.3609,
        "rooms": 3,
        "area": 85.0,
        "floor": 7,
        "total_floors": 12,
        "price": 32.5,
        "series": "1-ЛГ-505",
        "year_built": 1955,
        "wall_type": "Кирпич",
        "has_lift": True,
        "has_balcony": True,
        "photo_url": None,
        "top_issues": ["Хорошая звукоизоляция", "Просторные комнаты", "Двор-колодец"],
        "dist_metro_m": 200,
        "schools_1km": 5,
        "parks_1km": 3,
        "shops_1km": 25,
        "reputation_score": 92
    },
    {
        "id": 3,
        "name": "ул. Восстания, д. 10",
        "address": "ул. Восстания, д. 10",
        "lat": 59.9317,
        "lon": 30.3605,
        "rooms": 1,
        "area": 45.0,
        "floor": 3,
        "total_floors": 7,
        "price": 11.2,
        "series": "137",
        "year_built": 1970,
        "wall_type": "Панель",
        "has_lift": False,
        "has_balcony": True,
        "photo_url": None,
        "top_issues": ["Шумно от соседей", "Требуется ремонт", "Хорошее расположение"],
        "dist_metro_m": 500,
        "schools_1km": 3,
        "parks_1km": 1,
        "shops_1km": 8,
        "reputation_score": 68
    }
]

df = pd.DataFrame(buildings_data)

# === ЗАГОЛОВОК ===
st.title("Рынок жилой недвижимости Санкт-Петербурга")
st.caption("Прототип аналитической системы | ФКТИ СПбГЭТУ «ЛЭТИ» | 2026")

# === БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ===
with st.sidebar:
    st.header("Фильтры")
    
    st.subheader("Бюджет (млн ₽)")
    min_price = float(df['price'].min())
    max_price = float(df['price'].max())
    budget_range = st.slider("", min_price, max_price, (min_price, max_price), key="budget")
    
    st.subheader("Мин. рейтинг репутации")
    min_rating = st.slider("", 0, 100, 0, key="rating")
    
    st.subheader("Год постройки")
    min_year = int(df['year_built'].min())
    max_year = int(df['year_built'].max())
    year_range = st.slider("", min_year, max_year, (min_year, max_year), key="year")
    
    st.subheader("Количество комнат")
    col1, col2, col3 = st.columns(3)
    with col1:
        rooms_1 = st.checkbox("1", key="rooms_1")
    with col2:
        rooms_2 = st.checkbox("2", key="rooms_2")
    with col3:
        rooms_3 = st.checkbox("3", key="rooms_3")
    
    selected_rooms = []
    if rooms_1: selected_rooms.append(1)
    if rooms_2: selected_rooms.append(2)
    if rooms_3: selected_rooms.append(3)

# === ПРИМЕНЕНИЕ ФИЛЬТРОВ ===
filtered_df = df[
    (df['price'] >= budget_range[0]) & 
    (df['price'] <= budget_range[1]) &
    (df['year_built'] >= year_range[0]) & 
    (df['year_built'] <= year_range[1]) &
    (df['reputation_score'] >= min_rating)
]

if selected_rooms:
    filtered_df = filtered_df[filtered_df['rooms'].isin(selected_rooms)]

# === ОСНОВНАЯ ОБЛАСТЬ ===
col_map, col_card = st.columns([2, 1])

with col_map:
    st.subheader("🗺️ Карта объектов")
    
    # Создаём карту
    m = folium.Map(location=[59.9343, 30.3351], zoom_start=13, tiles="OpenStreetMap")
    
    for _, row in filtered_df.iterrows():
        # Цвет маркера в зависимости от репутации
        if row['reputation_score'] >= 70:
            color = "green"
        elif row['reputation_score'] >= 50:
            color = "orange"
        else:
            color = "red"
        
        # Tooltip при наведении
        tooltip_text = f"""
        <b>{row['name']}</b><br>
        💰 {row['price']} млн ₽<br>
        🛏️ {row['rooms']} комн. |  {row['area']} м²<br>
        📅 {row['year_built']} г.
        """
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            tooltip=tooltip_text,
            popup=row['name']
        ).add_to(m)
    
    # Отображаем карту
    map_data = st_folium(m, width="100%", height=450, key="map")
    
    # Обработка клика по карте
    selected_id = None
    if map_data and map_data.get("last_object_clicked"):
        popup_name = map_data["last_object_clicked"].get("popup")
        if popup_name:
            selected_row = filtered_df[filtered_df['name'] == popup_name]
            if not selected_row.empty:
                selected_id = selected_row.iloc[0]['id']
    
    # ВЫПАДАЮЩИЙ СПИСОК ПОД КАРТОЙ
    if not filtered_df.empty:
        # Находим индекс выбранного объекта
        current_index = 0
        if selected_id is not None:
            idx_list = filtered_df[filtered_df['id'] == selected_id].index
            if not idx_list.empty:
                current_index = idx_list[0]
        
        selected_address = st.selectbox(
            "Выберите объект из списка:",
            options=filtered_df['name'].tolist(),
            index=current_index,
            key="object_select"
        )
        
        if selected_address:
            selected_row = filtered_df[filtered_df['name'] == selected_address].iloc[0]
            selected_id = selected_row['id']
    else:
        st.warning("⚠️ Нет объектов, соответствующих фильтрам")
        selected_id = None

with col_card:
    if selected_id is not None:
        prop = filtered_df[filtered_df['id'] == selected_id].iloc[0]
        
        # Название и цена (без подзаголовка "Карточка предложения")
        st.markdown(f"### 📍{prop['name']}")
        st.info(f"{prop['rooms']}-комн. | 📐 {prop['area']} м² | {prop['floor']}/{prop['total_floors']} эт. | 💰 {prop['price']} млн ₽")
        
        st.divider()
        
        # Общая информация и фото
        col_info, col_photo = st.columns(2)
        
        with col_info:
            st.markdown("**🏗️ Общая информация**")
            st.text(f"Серия: {prop['series']}")
            st.text(f"Год постройки: {prop['year_built']}")
            st.text(f"Стены: {prop['wall_type']}")
            
            lift_icon = "✅" if prop['has_lift'] else "❌"
            balcony_icon = "✅" if prop['has_balcony'] else "❌"
            st.text(f"Лифт: {lift_icon} | Балкон: {balcony_icon}")
        
        with col_photo:
            st.markdown("**🖼️ Фото**")
            # Заглушка для фото
            st.image("https://placehold.co/300x200/e0e7ff/1e3a8a?text=Фото+объекта", use_container_width=True)
        
        st.divider()
        
        # Отзывы о доме (теги)
        st.markdown("**🗣️ Отзывы о доме**")
        if prop['top_issues']:
            tags_html = "".join([
                f'<span style="background:#e0e7ff; color:#1e3a8a; padding:4px 8px; border-radius:6px; margin:2px; display:inline-block; font-size:0.85em;">{tag}</span>' 
                for tag in prop['top_issues']
            ])
            st.markdown(f"<div style='line-height:1.8;'>{tags_html}</div>", unsafe_allow_html=True)
        else:
            st.caption("Нет данных об отзывах")
        
        st.divider()
        
        # Инфраструктура
        st.markdown("**🏪 Инфраструктура (радиус 1 км)**")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("🚇 До метро", f"{prop['dist_metro_m']} м")
        with col_m2:
            st.metric("🏫 Школы", prop['schools_1km'])
        with col_m3:
            st.metric("🌲 Парки", prop['parks_1km'])
        with col_m4:
            st.metric("🛒 Магазины", prop['shops_1km'])
        
        st.divider()
        
        # Ссылка на объявление
        st.link_button("🔗 Открыть оригинальное объявление", "https://cian.ru", use_container_width=True)
    
    else:
        st.info("👆 Нажмите на маркер на карте или выберите из списка, чтобы открыть карточку объекта.")

# === ОТОБРАЖЕНИЕ ТЕКУЩИХ ФИЛЬТРОВ ===
with st.expander("📊 Текущие параметры фильтрации"):
    st.write(f"💰 Бюджет: {budget_range[0]} - {budget_range[1]} млн ₽")
    st.write(f"⭐ Мин. рейтинг: {min_rating}")
    st.write(f"🏗️ Год постройки: {year_range[0]} - {year_range[1]}")
    st.write(f"🛏️ Комнаты: {', '.join(map(str, selected_rooms)) if selected_rooms else 'любые'}")
    st.write(f"📊 Найдено объектов: {len(filtered_df)}")
