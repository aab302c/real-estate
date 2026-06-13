import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Рынок жилой недвижимости СПб",
    page_icon="🏠",
    layout="wide"
)

# === ГЕНЕРАЦИЯ 130 ТОЧЕК В ЦЕНТРЕ СПБ ===
center_lat, center_lon = 59.9343, 30.3351

# Базовые адреса для названий (чтобы не придумывать каждый раз)
street_names = [
    "наб. реки Фонтанки", "Невский пр.", "ул. Восстания", "Литейный пр.",
    "Владимирский пр.", "ул. Рубинштейна", "Загородный пр.", "ул. Марата",
    "ул. Садовая", "Гороховая ул.", "Большая Морская ул.", "Малая Морская ул.",
    "Каменноостровский пр.", "ул. Чайковского", "Фурштатская ул.", "Кирочная ул."
]

series_options = ["1-ЛГ-505", "137", "600", "1-ЛГ-600", "II-18", "II-32"]
wall_options = ["Кирпич", "Панель", "Блок"]

# Проблемы для тегов по цветам
issues_by_color = {
    "green": ["Хорошая шумоизоляция", "Уютный двор", "Чистый подъезд", "Тихо", "Светлые комнаты", "Ремонт", "Новый лифт"],
    "yellow": ["Шумновато", "Старые коммуникации", "Требуется ремонт", "Лифт старый", "Парковки мало"],
    "red": ["Шумно от соседей", "Плесень", "Протекает крыша", "Грязный подъезд", "Лифт не работает", "Слышимость"]
}

buildings_data = []
building_id = 1

# Цвета с весами: 50% зелёные, 30% жёлтые, 20% красные
color_weights = ["green", "green", "green", "green", "green", "yellow", "yellow", "yellow", "red", "red"]

for i in range(130):
    # Координаты в радиусе ~2.5 км от центра
    lat = center_lat + random.uniform(-0.025, 0.025)
    lon = center_lon + random.uniform(-0.03, 0.03)
    
    # Цвет с весами
    color = random.choice(color_weights)
    
    # Репутация в зависимости от цвета
    if color == "green":
        reputation = random.randint(70, 100)
    elif color == "yellow":
        reputation = random.randint(50, 69)
    else:
        reputation = random.randint(0, 49)
    
    # Генерация адреса
    street = random.choice(street_names)
    house_num = random.randint(1, 120)
    address = f"{street}, {house_num}"
    if random.random() > 0.85:
        address += f" {random.choice(['к.1', 'к.2', 'лит.А'])}"
    
    # Цена в зависимости от репутации
    if reputation >= 80:
        price = round(random.uniform(18, 45), 1)
    elif reputation >= 50:
        price = round(random.uniform(10, 25), 1)
    else:
        price = round(random.uniform(5, 15), 1)
    
    # Площадь
    area = round(random.uniform(35, 110), 1)
    
    # Комнаты
    if area < 45:
        rooms = 1
    elif area < 70:
        rooms = 2
    else:
        rooms = 3
    
    # Год постройки
    if reputation >= 80:
        year = random.randint(2000, 2020)
    elif reputation >= 50:
        year = random.randint(1980, 2005)
    else:
        year = random.randint(1950, 1990)
    
    # Проблемы (теги)
    issues = random.sample(issues_by_color[color], min(3, len(issues_by_color[color])))
    
    buildings_data.append({
        "id": building_id,
        "name": address,
        "address": address,
        "lat": lat,
        "lon": lon,
        "rooms": rooms,
        "area": area,
        "floor": random.randint(1, 12),
        "total_floors": random.randint(5, 14),
        "price": price,
        "series": random.choice(series_options),
        "year_built": year,
        "wall_type": random.choice(wall_options),
        "has_lift": random.choice([True, False]),
        "has_balcony": random.choice([True, False]),
        "photo_url": None,
        "top_issues": issues,
        "dist_metro_m": random.randint(100, 800),
        "schools_1km": random.randint(1, 8),
        "parks_1km": random.randint(0, 5),
        "shops_1km": random.randint(3, 20),
        "reputation_score": reputation
    })
    building_id += 1

df = pd.DataFrame(buildings_data)

# === ЗАГОЛОВОК ===
st.title("🏠 Рынок жилой недвижимости СПб")
st.caption("Прототип аналитической системы | СПбГЭТУ «ЛЭТИ» | 2026")

# === БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ===
with st.sidebar:
    st.header("📊 Фильтры")
    
    st.subheader("💰 Бюджет (млн ₽)")
    min_price = float(df['price'].min())
    max_price = float(df['price'].max())
    budget_range = st.slider("", min_price, max_price, (min_price, max_price), key="budget")
    
    st.subheader("⭐ Мин. рейтинг репутации")
    min_rating = st.slider("", 0, 100, 0, key="rating")
    
    st.subheader("🏗️ Год постройки")
    min_year = int(df['year_built'].min())
    max_year = int(df['year_built'].max())
    year_range = st.slider("", min_year, max_year, (min_year, max_year), key="year")
    
    st.subheader("🛏️ Количество комнат")
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
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
    
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
        🛏️ {row['rooms']} комн. | 📐 {row['area']} м²<br>
        📅 {row['year_built']} г.
        """
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            tooltip=tooltip_text,
            popup=row['name']
        ).add_to(m)
    
    # Отображаем карту
    map_data = st_folium(m, width="100%", height=500, key="map")
    
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
        
        st.markdown(f"### 📍 {prop['name']}")
        st.info(f"{prop['rooms']}-комн. | 📐 {prop['area']} м² | {prop['floor']}/{prop['total_floors']} эт. | 💰 {prop['price']} млн ₽")
        
        st.divider()
        
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
            st.image("https://placehold.co/300x200/e0e7ff/1e3a8a?text=Фото+объекта", use_container_width=True)
        
        st.divider()
        
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
