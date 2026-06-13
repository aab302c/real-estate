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

# === ФУНКЦИЯ ДЛЯ ПАРСИНГА АДРЕСА ===
def parse_address(full_address):
    """
    Извлекает из полного адреса улицу и номер дома.
    Пример: "Санкт-Петербург, р-н Центральный, № 78, м. Сенная площадь, набережная Реки Фонтанки, 73"
    Результат: улица = "набережная Реки Фонтанки", дом = "73"
    """
    parts = full_address.split(',')
    if len(parts) >= 2:
        street = parts[-2].strip()  # предпоследняя часть
        house = parts[-1].strip()    # последняя часть
        return street, house
    return full_address, ""

# === ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ КООРДИНАТ ПО РАЙОНУ ===
def get_coords_from_address(address):
    """
    Определяет координаты на основе района в адресе
    """
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
    return [59.9343, 30.3351]  # центр СПб по умолчанию

# === ДАННЫЕ ===
buildings_data = [
    {"id": 1, "address": "Санкт-Петербург, р-н Кировский, Автово, м. Путиловская, улица Васи Алексеева, 14", "price": 18750000, "year_built": 1957, "reputation_score": 65, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-ulica-vasi-alekseeva-2867778995-1.jpg", "top_issues": ["Хорошее расположение", "Требуется ремонт"], "dist_metro_m": 500, "schools_1km": 3, "parks_1km": 2, "shops_1km": 8},
    {"id": 2, "address": "Санкт-Петербург, р-н Калининский, Прометей, м. Гражданский проспект, Светлановский проспект, 109К1", "price": 14500000, "year_built": 1972, "reputation_score": 70, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-svetlanovskiy-prospekt-2886157144-1.jpg", "top_issues": ["Уютный двор", "Чистый подъезд"], "dist_metro_m": 400, "schools_1km": 4, "parks_1km": 3, "shops_1km": 12},
    {"id": 3, "address": "Санкт-Петербург, р-н Красногвардейский, Пороховые, м. Ладожская, Индустриальный проспект, 29", "price": 4750000, "year_built": 1981, "reputation_score": 55, "rooms": 2, "area": 53.0, "floor": 4, "total_floors": 16, "series": "137", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-industrialnyy-prospekt-2187124990-1.jpg", "top_issues": ["Шумновато", "Старые коммуникации"], "dist_metro_m": 600, "schools_1km": 2, "parks_1km": 1, "shops_1km": 5},
    {"id": 4, "address": "Санкт-Петербург, р-н Адмиралтейский, Адмиралтейский, м. Садовая, набережная Канала Грибоедова, 84", "price": 21566000, "year_built": 0, "reputation_score": 85, "rooms": 2, "area": 52.6, "floor": 3, "total_floors": 4, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2826664576-1.jpg", "top_issues": ["Хорошая звукоизоляция", "Светлые комнаты", "Ремонт"], "dist_metro_m": 300, "schools_1km": 5, "parks_1km": 3, "shops_1km": 15},
    {"id": 5, "address": "Санкт-Петербург, р-н Центральный, Владимирский, м. Достоевская, улица Рубинштейна, 13", "price": 17900000, "year_built": 1869, "reputation_score": 80, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-ulica-rubinshteyna-2856621331-1.jpg", "top_issues": ["Исторический центр", "Высокие потолки"], "dist_metro_m": 250, "schools_1km": 6, "parks_1km": 2, "shops_1km": 20},
    {"id": 6, "address": "Санкт-Петербург, р-н Невский, Обуховский, м. Пролетарская, улица Бабушкина, 100", "price": 7500000, "year_built": 1963, "reputation_score": 45, "rooms": 2, "area": 45.7, "floor": 3, "total_floors": 5, "series": "", "wall_type": "Панель", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2874655762-1.jpg", "top_issues": ["Шумно от соседей", "Старый лифт"], "dist_metro_m": 700, "schools_1km": 2, "parks_1km": 1, "shops_1km": 4},
    {"id": 7, "address": "Санкт-Петербург, р-н Центральный, Дворцовый, м. Гостиный двор, Большая Конюшенная улица, 25", "price": 24000000, "year_built": 1877, "reputation_score": 90, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-bolshaya-konyushennaya-ulica-2851602908-1.jpg", "top_issues": ["Элитный центр", "Двор-колодец"], "dist_metro_m": 200, "schools_1km": 7, "parks_1km": 3, "shops_1km": 25},
    {"id": 8, "address": "Санкт-Петербург, р-н Центральный, Смольнинское, м. Чернышевская, улица Восстания, 43", "price": 50000000, "year_built": 1874, "reputation_score": 95, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2891148487-1.jpg", "top_issues": ["Престижный район", "Качественная планировка"], "dist_metro_m": 150, "schools_1km": 8, "parks_1km": 4, "shops_1km": 30},
    {"id": 9, "address": "Санкт-Петербург, р-н Московский, Гагаринское, м. Московская, Бассейная улица, 63", "price": 8990000, "year_built": 1962, "reputation_score": 60, "rooms": 2, "area": 45.5, "floor": 4, "total_floors": 5, "series": "", "wall_type": "", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-basseynaya-ulica-2892562681-1.jpg", "top_issues": ["Требуется ремонт", "Старые коммуникации"], "dist_metro_m": 450, "schools_1km": 3, "parks_1km": 2, "shops_1km": 7},
    {"id": 10, "address": "Санкт-Петербург, р-н Центральный, Литейный, м. Чернышевская, улица Рылеева, 6", "price": 38900000, "year_built": 1846, "reputation_score": 92, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892281102-1.jpg", "top_issues": ["Исторический центр", "Дорого и качественно"], "dist_metro_m": 180, "schools_1km": 6, "parks_1km": 3, "shops_1km": 22},
    {"id": 11, "address": "Санкт-Петербург, р-н Петроградский, Кронверкское, м. Горьковская, Сытнинская площадь, 3", "price": 41500000, "year_built": 1877, "reputation_score": 88, "rooms": 2, "area": 104.0, "floor": 3, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2820229159-1.jpg", "top_issues": ["Просторные комнаты", "Центр города"], "dist_metro_m": 350, "schools_1km": 5, "parks_1km": 3, "shops_1km": 18},
    {"id": 12, "address": "Санкт-Петербург, р-н Красногвардейский, Малая Охта, м. Новочеркасская, проспект Шаумяна, 67", "price": 7750000, "year_built": 1960, "reputation_score": 50, "rooms": 2, "area": 45.8, "floor": 3, "total_floors": 5, "series": "1-335", "wall_type": "Панель", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892505528-1.jpg", "top_issues": ["Бюджетный вариант", "Требуется ремонт"], "dist_metro_m": 550, "schools_1km": 2, "parks_1km": 1, "shops_1km": 4},
    {"id": 13, "address": "Санкт-Петербург, р-н Адмиралтейский, Коломна, м. Балтийская, набережная Реки Фонтанки, 179", "price": 17700000, "year_built": 1912, "reputation_score": 78, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-naberezhnaya-reki-fontanki-2880781431-1.jpg", "top_issues": ["Вид на Фонтанку", "Исторический центр"], "dist_metro_m": 400, "schools_1km": 4, "parks_1km": 2, "shops_1km": 12},
    {"id": 14, "address": "Санкт-Петербург, р-н Фрунзенский, Волковское, м. Волковская, Волковский проспект, 14", "price": 9000000, "year_built": 1917, "reputation_score": 58, "rooms": 2, "area": 51.5, "floor": 4, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-volkovskiy-prospekt-2864927880-1.jpg", "top_issues": ["Старый фонд", "Хорошая планировка"], "dist_metro_m": 480, "schools_1km": 3, "parks_1km": 2, "shops_1km": 6},
    {"id": 15, "address": "Санкт-Петербург, р-н Невский, Народный, м. Ломоносовская, проспект Большевиков, 59К1", "price": 7100000, "year_built": 1963, "reputation_score": 48, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "од-6", "wall_type": "", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892370398-1.jpg", "top_issues": ["Дешево", "Недалеко от метро"], "dist_metro_m": 650, "schools_1km": 2, "parks_1km": 1, "shops_1km": 5},
    {"id": 16, "address": "Санкт-Петербург, р-н Приморский, Юнтолово, м. Комендантский проспект, проспект Королева, 54К1", "price": 15550000, "year_built": 1989, "reputation_score": 72, "rooms": 2, "area": 45.8, "floor": 4, "total_floors": 9, "series": "1лг-504", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2887193881-1.jpg", "top_issues": ["Новостройка", "Развитая инфраструктура"], "dist_metro_m": 300, "schools_1km": 4, "parks_1km": 3, "shops_1km": 10},
    {"id": 17, "address": "Санкт-Петербург, р-н Центральный, № 78, м. Сенная площадь, набережная Реки Фонтанки, 73", "price": 31000000, "year_built": 1828, "reputation_score": 86, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892920324-1.jpg", "top_issues": ["Центр", "Вид на Фонтанку"], "dist_metro_m": 280, "schools_1km": 6, "parks_1km": 3, "shops_1km": 20},
    {"id": 18, "address": "Санкт-Петербург, р-н Приморский, Чёрная речка, м. Черная речка, Лисичанская улица, 8", "price": 8500000, "year_built": 1899, "reputation_score": 62, "rooms": 2, "area": 39.7, "floor": 5, "total_floors": 6, "series": "", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-lisichanskaya-ulica-2853417402-1.jpg", "top_issues": ["Дореволюционный дом", "Высокие потолки"], "dist_metro_m": 380, "schools_1km": 3, "parks_1km": 2, "shops_1km": 8},
    {"id": 19, "address": "Санкт-Петербург, р-н Петроградский, Посадский, м. Горьковская, Мичуринская улица, 1", "price": 32900000, "year_built": 1951, "reputation_score": 83, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2872319947-1.jpg", "top_issues": ["Сталинский дом", "Петроградская сторона"], "dist_metro_m": 320, "schools_1km": 5, "parks_1km": 4, "shops_1km": 15},
    {"id": 20, "address": "Санкт-Петербург, р-н Петроградский, Посадский, м. Горьковская, улица Куйбышева, 1/5", "price": 26900000, "year_built": 1955, "reputation_score": 80, "rooms": 0, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2871870239-1.jpg", "top_issues": ["Сталинка", "Хорошая планировка"], "dist_metro_m": 340, "schools_1km": 5, "parks_1km": 3, "shops_1km": 16},
]

# === ОБРАБОТКА ДАННЫХ ===
for building in buildings_data:
    # Определяем координаты
    lat, lon = get_coords_from_address(building["address"])
    building["lat"] = lat
    building["lon"] = lon
    
    # Парсим адрес: извлекаем улицу и номер дома
    street, house = parse_address(building["address"])
    building["street"] = street
    building["house"] = house
    
    # Короткое название для отображения
    building["short_name"] = f"{street}, {house}"
    
    # Цвет в зависимости от репутации
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
    with col2:
        rooms_2 = st.checkbox("2", key="rooms_2")
    with col3:
        rooms_3 = st.checkbox("3", key="rooms_3")
    
    selected_rooms = []
    if rooms_1: selected_rooms.append(1)
    if rooms_2: selected_rooms.append(2)
    if rooms_3: selected_rooms.append(3)

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
    
    for _, row in filtered_df.iterrows():
        tooltip_text = f"""
        <b>{row['short_name']}</b><br>
        💰 {row['price']/1e6:.1f} млн ₽<br>
        🏗️ {int(row['year_built']) if row['year_built'] > 0 else 'н/д'} г.<br>
        ⭐ {row['reputation_score']}
        """
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
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
    
    selected_id = None
    if map_data and map_data.get("last_object_clicked"):
        popup_name = map_data["last_object_clicked"].get("popup")
        if popup_name:
            selected_row = filtered_df[filtered_df['short_name'] == popup_name]
            if not selected_row.empty:
                selected_id = selected_row.iloc[0]['id']
    
    if not filtered_df.empty:
        current_index = 0
        if selected_id is not None:
            idx_list = filtered_df[filtered_df['id'] == selected_id].index
            if not idx_list.empty:
                current_index = idx_list[0]
        
        selected_short_name = st.selectbox(
            "Выберите объект из списка:",
            options=filtered_df['short_name'].tolist(),
            index=current_index,
            key="object_select"
        )
        
        if selected_short_name:
            selected_row = filtered_df[filtered_df['short_name'] == selected_short_name].iloc[0]
            selected_id = selected_row['id']
    else:
        st.warning("⚠️ Нет объектов, соответствующих фильтрам")
        selected_id = None

# === КАРТОЧКА ===
with col_card:
    if selected_id is not None:
        prop = filtered_df[filtered_df['id'] == selected_id].iloc[0]
        
        st.markdown(f"### 📍 {prop['short_name']}")
        
        price_m = prop['price'] / 1e6
        rooms = int(prop['rooms']) if prop['rooms'] > 0 else "н/д"
        area = prop['area'] if prop['area'] > 0 else "н/д"
        floor = int(prop['floor']) if prop['floor'] > 0 else "н/д"
        total_floors = int(prop['total_floors']) if prop['total_floors'] > 0 else "н/д"
        
        st.info(f"{rooms}-комн. | 📐 {area} м² | {floor}/{total_floors} эт. | 💰 {price_m:.1f} млн ₽")
        
        st.divider()
        
        col_info, col_photo = st.columns(2)
        
        with col_info:
            st.markdown("**🏗️ Общая информация**")
            st.text(f"Серия: {prop['series'] if prop['series'] else 'н/д'}")
            st.text(f"Год постройки: {int(prop['year_built']) if prop['year_built'] > 0 else 'н/д'}")
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
        st.info("👆 Нажмите на маркер на карте или выберите из списка, чтобы открыть карточку объекта.")

# === СТАТИСТИКА ===
with st.expander("📊 Текущие параметры фильтрации"):
    st.write(f"💰 Бюджет: {budget_range[0]:.1f} - {budget_range[1]:.1f} млн ₽")
    st.write(f"⭐ Мин. рейтинг: {min_rating}")
    st.write(f"🛏️ Комнаты: {', '.join(map(str, selected_rooms)) if selected_rooms else 'любые'}")
    st.write(f"📊 Найдено объектов: {len(filtered_df)}")
    
    if not filtered_df.empty:
        green = len(filtered_df[filtered_df['reputation_score'] >= 70])
        yellow = len(filtered_df[(filtered_df['reputation_score'] >= 50) & (filtered_df['reputation_score'] < 70)])
        red = len(filtered_df[filtered_df['reputation_score'] < 50])
        st.write(f"🟢 Зелёных: {green} ({green/len(filtered_df)*100:.0f}%)")
        st.write(f"🟡 Жёлтых: {yellow} ({yellow/len(filtered_df)*100:.0f}%)")
        st.write(f"🔴 Красных: {red} ({red/len(filtered_df)*100:.0f}%)")
