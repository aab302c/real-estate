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

# === ФУНКЦИЯ ДЛЯ ПАРСИНГА АДРЕСА ===
def parse_address(full_address):
    parts = full_address.split(',')
    if len(parts) >= 2:
        street = parts[-2].strip()
        house = parts[-1].strip()
        return street, house
    return full_address, ""

# === ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ КООРДИНАТ ===
def get_coords_from_address(address):
    district_coords = {
        "Кировский": [59.8764, 30.2614],
        "Калининский": [59.9975, 30.3968],
        "Красногвардейский": [59.9639, 30.4998],
        "Адмиралтейский": [59.9343, 30.3050],
        "Центральный": [59.9343, 30.3351],
        "Невский": [59.8731, 30.4885],
        "Московский": [59.8528, 30.3228],
        "Петроградский": [59.9639, 30.3115],
        "Приморский": [60.0044, 30.2927],
        "Василеостровский": [59.9417, 30.2756],
        "Выборгский": [60.0036, 30.2919],
        "Фрунзенский": [59.8961, 30.3675],
        "Красносельский": [59.8745, 30.1394],
        "Пушкинский": [59.7234, 30.4122],
    }
    for district, coords in district_coords.items():
        if district in address:
            return coords
    return [59.9343, 30.3351]

# === ДАННЫЕ ===
buildings_data = [
    {"id": 1, "address": "Санкт-Петербург, р-н Кировский, Автово, м. Путиловская, улица Васи Алексеева, 14", "price": 18750000, "year_built": 1957, "reputation_score": 65, "rooms": 4, "area": 120, "floor": 1, "total_floors": 1, "series": "индивидуальный проект", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-ulica-vasi-alekseeva-2867778995-1.jpg", "top_issues": ["Хорошее расположение", "Требуется ремонт"], "dist_metro_m": 500, "schools_1km": 3, "parks_1km": 2, "shops_1km": 8},
    {"id": 2, "address": "Санкт-Петербург, р-н Центральный, Невский пр., 100", "price": 25000000, "year_built": 2000, "reputation_score": 85, "rooms": 3, "area": 95, "floor": 5, "total_floors": 9, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": True, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-nevskiy-prospekt-2892920324-1.jpg", "top_issues": ["Хороший вид", "Просторные комнаты"], "dist_metro_m": 200, "schools_1km": 4, "parks_1km": 2, "shops_1km": 15},
]

# === ОБРАБОТКА ДАННЫХ ===
for building in buildings_data:
    lat, lon = get_coords_from_address(building["address"])
    building["lat"] = lat
    building["lon"] = lon
    
    street, house = parse_address(building["address"])
    building["street"] = street
    building["house"] = house
    building["short_name"] = f"{street}, {house}"
    
    if building["reputation_score"] >= 70:
        building["color"] = "green"
    elif building["reputation_score"] >= 50:
        building["color"] = "orange"
    else:
        building["color"] = "red"

df = pd.DataFrame(buildings_data)

# === ЗАГОЛОВОК ===
st.title("🏠 Рынок жилой недвижимости СПб")
st.caption("Прототип аналитической системы | СПбГЭТУ «ЛЭТИ» | 2026")

# === БОКОВАЯ ПАНЕЛЬ ===
with st.sidebar:
    st.header("📊 Фильтры")
    
    min_price = float(df['price'].min())
    max_price = float(df['price'].max())
    budget_range = st.slider("💰 Бюджет (млн ₽)", min_price/1e6, max_price/1e6, (min_price/1e6, max_price/1e6), key="budget")
    
    min_rating = st.slider("⭐ Мин. рейтинг репутации", 0, 100, 0, key="rating")
    
    st.subheader("🛏️ Количество комнат")
    col1, col2, col3 = st.columns(3)
    with col1:
        rooms_1 = st.checkbox("1", key="rooms_1")
        rooms_4 = st.checkbox("4", key="rooms_4")
    with col2:
        rooms_2 = st.checkbox("2", key="rooms_2")
    with col3:
        rooms_3 = st.checkbox("3", key="rooms_3")
    
    selected_rooms = []
    if rooms_1: selected_rooms.append(1)
    if rooms_2: selected_rooms.append(2)
    if rooms_3: selected_rooms.append(3)
    if rooms_4: selected_rooms.append(4)

# === ФИЛЬТРАЦИЯ ===
filtered_df = df[
    (df['price']/1e6 >= budget_range[0]) & 
    (df['price']/1e6 <= budget_range[1]) &
    (df['reputation_score'] >= min_rating)
]

if selected_rooms:
    filtered_df = filtered_df[filtered_df['rooms'].isin(selected_rooms)]

# === КАРТА ===
col_map, col_card = st.columns([2, 1])

with col_map:
    st.subheader("🗺️ Карта объектов")
    
    m = folium.Map(location=[59.9343, 30.3351], zoom_start=11, tiles="OpenStreetMap")
    
    for idx, row in filtered_df.iterrows():
        lat = row['lat'] + (idx * 0.0005) % 0.005
        lon = row['lon'] + (idx * 0.0003) % 0.005
        
        tooltip_text = f"""
        <b>{row['short_name']}</b><br>
        💰 {row['price']/1e6:.1f} млн ₽<br>
        🛏️ {row['rooms']} комн. | 📐 {row['area']} м²<br>
        ⭐ {row['reputation_score']}
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=row['color'],
            fill=True,
            fill_color=row['color'],
            fill_opacity=0.7,
            weight=2,
            tooltip=tooltip_text,
            popup=row['short_name']
        ).add_to(m)
    
    map_data = st_folium(m, width="100%", height=500, key="map")
    
    # Обработка клика по карте
    selected_id = None
    if map_data and map_data.get("last_object_clicked"):
        popup_name = map_data["last_object_clicked"].get("popup")
        if popup_name:
            selected_row = filtered_df[filtered_df['short_name'] == popup_name]
            if not selected_row.empty:
                selected_id = selected_row.iloc[0]['id']
    
    # === ВЫПАДАЮЩИЙ СПИСОК С ПУСТЫМ ЭЛЕМЕНТОМ ===
    if not filtered_df.empty:
        # Добавляем пустой элемент в начало
        options_list = ["-- Выберите объект --"] + filtered_df['short_name'].tolist()
        
        current_index = 0
        selected_short_name = st.selectbox(
            "Выберите объект из списка:",
            options=options_list,
            index=current_index,
            key="object_select"
        )
        
        if selected_short_name and selected_short_name != "-- Выберите объект --":
            selected_row = filtered_df[filtered_df['short_name'] == selected_short_name].iloc[0]
            selected_id = selected_row['id']
        else:
            selected_id = None
    else:
        st.warning("⚠️ Нет объектов, соответствующих фильтрам")
        selected_id = None

# === КАРТОЧКА ОБЪЕКТА ===
with col_card:
    if selected_id is not None:
        prop = filtered_df[filtered_df['id'] == selected_id].iloc[0]
        
        st.markdown(f"### 📍 {prop['short_name']}")
        
        price_m = prop['price'] / 1e6
        rooms = prop['rooms']
        area = prop['area']
        floor = prop['floor']
        total_floors = prop['total_floors']
        
        st.info(f"{rooms}-комн. | 📐 {area} м² | {floor}/{total_floors} эт. | 💰 {price_m:.1f} млн ₽")
        
        st.divider()
        
        col_info, col_photo = st.columns(2)
        
        with col_info:
            st.markdown("**🏗️ Общая информация**")
            st.text(f"Серия: {prop['series'] if prop['series'] else 'н/д'}")
            st.text(f"Год постройки: {prop['year_built']}")
            st.text(f"Стены: {prop['wall_type'] if prop['wall_type'] else 'н/д'}")
            
            lift_icon = "✅" if prop['has_lift'] else "❌"
            balcony_icon = "✅" if prop['has_balcony'] else "❌"
            st.text(f"Лифт: {lift_icon} | Балкон: {balcony_icon}")
        
        with col_photo:
            st.markdown("**🖼️ Фото**")
            if prop['photo_url']:
                st.image(prop['photo_url'], use_container_width=True)
            else:
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
        st.info("👆 Выберите объект на карте или из списка, чтобы открыть карточку.")

# === СТАТИСТИКА ===
with st.expander("📊 Текущие параметры фильтрации"):
    st.write(f"💰 Бюджет: {budget_range[0]:.1f} - {budget_range[1]:.1f} млн ₽")
    st.write(f"⭐ Мин. рейтинг: {min_rating}")
    st.write(f"🛏️ Комнаты: {', '.join(map(str, selected_rooms)) if selected_rooms else 'любые'}")
    st.write(f"📊 Найдено объектов: {len(filtered_df)}")
