import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from sqlalchemy import create_engine
import re

def aggregate_tags(tags_string):
    """
    Агрегирует теги по аспекту и возвращает доминирующий цвет + процент.
    Вход: "Шумоизоляция|green; Шумоизоляция|grey; Кухня|grey; Кухня|red"
    Выход: ["Шумоизоляция|green|67%", "Кухня|red|50%"]
    """
    if not tags_string or pd.isna(tags_string):
        return []
    
    # Разбиваем на отдельные теги
    tags = [t.strip() for t in str(tags_string).split(';') if t.strip()]
    
    # Группируем по аспекту
    aspects = {}
    for tag in tags:
        if '|' not in tag:
            continue
        aspect, color = tag.split('|', 1)
        if aspect not in aspects:
            aspects[aspect] = {'green': 0, 'red': 0, 'grey': 0}
        if color in aspects[aspect]:
            aspects[aspect][color] += 1
        else:
            aspects[aspect]['grey'] += 1  # fallback
    
    # Формируем результат
    result = []
    for aspect, colors in aspects.items():
        total = sum(colors.values())
        if total == 0:
            continue
        
        # Находим доминирующий цвет
        dominant_color = max(colors, key=colors.get)
        dominant_count = colors[dominant_color]
        percent = round(dominant_count / total * 100)
        
        # Если все цвета равны — оставляем серый
        if len([c for c in colors.values() if c > 0]) > 1 and dominant_count / total <= 0.5:
            dominant_color = 'grey'
            percent = 50
        
        result.append(f"{aspect}|{dominant_color}|{percent}%")
    
    return result

def render_colored_tags_with_percent(tags_list):
    """Отображает теги с процентами"""
    if not tags_list:
        return "Нет данных об отзывах"
    
    color_map = {
        'green': '#22c55e',
        'red': '#ef4444',
        'grey': '#6b7280',
    }
    
    html_parts = []
    for tag in tags_list:
        if '|' not in tag:
            continue
        
        parts = tag.split('|')
        aspect = parts[0]
        color = parts[1] if len(parts) > 1 else 'grey'
        percent = parts[2] if len(parts) > 2 else ''
        
        color_hex = color_map.get(color, '#6b7280')
        
        if percent:
            display_text = f"{aspect} {percent}"
        else:
            display_text = aspect
        
        html_parts.append(
            f'<span style="display:inline-block; background:#f3f4f6; '
            f'color:{color_hex}; padding:4px 14px; border-radius:16px; '
            f'margin:3px 6px 3px 0; font-size:0.85em; font-weight:500; '
            f'border:1px solid {color_hex}40;">{display_text}</span>'
        )
    
    return "".join(html_parts)
    
def render_colored_tags(tags_string):
    """Преобразует строку тегов вида 'aspect|color; aspect|color' в HTML с цветными плашками"""
    if not tags_string or pd.isna(tags_string):
        return "Нет данных об отзывах"
    
    # Цвета для текста
    color_map = {
        'green': '#22c55e',   # ярко-зеленый
        'red': '#ef4444',     # красный
        'grey': '#6b7280',    # серый
        'orange': '#f59e0b',  # оранжевый
        'blue': '#3b82f6',    # синий
    }
    
    # Разбиваем строку на отдельные теги
    tags = [t.strip() for t in str(tags_string).split(';') if t.strip()]
    
    html_parts = []
    for tag in tags:
        if '|' in tag:
            aspect, color = tag.split('|', 1)
            color_hex = color_map.get(color.lower(), '#6b7280')
            html_parts.append(
                f'<span style="display:inline-block; background:#f3f4f6; '
                f'color:{color_hex}; padding:4px 14px; border-radius:16px; '
                f'margin:3px 6px 3px 0; font-size:0.85em; font-weight:500; '
                f'border:1px solid {color_hex}40;">{aspect.strip()}</span>'
            )
        else:
            html_parts.append(
                f'<span style="display:inline-block; background:#f3f4f6; '
                f'color:#6b7280; padding:4px 14px; border-radius:16px; '
                f'margin:3px 6px 3px 0; font-size:0.85em; font-weight:500;">{tag}</span>'
            )
    
    return "".join(html_parts)
    
# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Рынок жилой недвижимости Санкт-Петербурга",
    page_icon="🏠",
    layout="wide"
)

# === ПОДКЛЮЧЕНИЕ К SUPABASE ===
DB_URL_SUPABASE = "postgresql://postgres.wtqngiewhatiufaeorcg:9zRV67GtDU1rUyHo@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"

@st.cache_data(ttl=600)
def load_data_from_supabase():
    """Загружает данные из Supabase"""
    engine = create_engine(DB_URL_SUPABASE)
    
    query = """
    SELECT 
        listing_id as id,
        price,
        area,
        rooms,
        floor,
        total_floors,
        housing_type,
        living_area,
        kitchen_area,
        metro_name,
        metro_time,
        photo_url,
        url,
        address,
        address_normalized,
        lat,
        lon,
        year_built,
        series_name as series,
        wall_type,
        top_issues,
        reputation_score,
        dist_metro_m,
        schools_1km,
        parks_1km,
        shops_1km
    FROM v_dashboard_data_v2  -- <--- ИЗМЕНЕНО НА v2
    WHERE lat IS NOT NULL AND lon IS NOT NULL
      AND lat BETWEEN 59.5 AND 60.5
      AND lon BETWEEN 29.5 AND 30.8
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    
    if df.empty:
        return df
    
    # === ФУНКЦИЯ ДЛЯ ПАРСИНГА АДРЕСА ===
    def parse_address(full_address):
        if not full_address:
            return "н/д", ""
        parts = full_address.split(',')
        if len(parts) >= 2:
            street = parts[-2].strip()
            house = parts[-1].strip()
            return street, house
        return full_address, ""
    
    # === ОБРАБОТКА ДАННЫХ ===
    df[['street', 'house']] = df['address'].apply(
        lambda x: pd.Series(parse_address(x))
    )
    df['short_name'] = df.apply(
        lambda row: f"{row['street']}, {row['house']}" if row['street'] != "н/д" else row['address_normalized'],
        axis=1
    )
    
    # Цвет по рейтингу
    def get_color(score):
        if score >= 70:
            return "green"
        elif score >= 45:
            return "orange"
        else:
            return "red"
    
    df['color'] = df['reputation_score'].apply(get_color)
    
    # Преобразуем top_issues из строки в список
    df['top_issues'] = df['top_issues'].apply(
        lambda x: [tag.strip() for tag in str(x).split(',') if tag.strip()] if x else []
    )
    
    # Заглушки
    df['has_lift'] = False
    df['has_balcony'] = False
    
    return df

# === ЗАГРУЗКА ДАННЫХ ===
with st.spinner("Загрузка данных..."):
    df = load_data_from_supabase()

if df.empty:
    st.error("❌ Нет данных. Проверь подключение к Supabase.")
    st.stop()

# === ЗАГОЛОВОК ===
st.title("Рынок жилой недвижимости Санкт-Петербурга")
st.caption("Прототип аналитической системы | ФКТИ СПбГЭТУ «ЛЭТИ» | 2026")

# === БОКОВАЯ ПАНЕЛЬ ===
with st.sidebar:
    st.header("Фильтры")
    
    min_rating = st.slider("Мин. рейтинг репутации", 0, 100, 0, key="rating")
    

    housing_types = df['housing_type'].dropna().unique().tolist()
    if not housing_types:
        housing_types = ["Вторичка"]
    selected_housing_types = st.multiselect(
        "Выберите тип жилья (можно несколько):",
        options=housing_types,
        default=housing_types,
        key="housing_multiselect"
    )
    
    min_price = float(df['price'].min())
    max_price = float(df['price'].max())
    budget_range = st.slider(
        "Бюджет (млн ₽)",
        min_price/1e6,
        max_price/1e6,
        (min_price/1e6, max_price/1e6),
        key="budget"
    )
    

    min_year = int(df['year_built'].min()) if df['year_built'].min() > 0 else 1900
    max_year = int(df['year_built'].max()) if df['year_built'].max() > 0 else 2024
    year_range = st.slider(
        "Выберите диапазон годов:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        key="year_range"
    )
    

    rooms_options = sorted(df['rooms'].dropna().unique().astype(int).tolist())
    selected_rooms = st.multiselect(
        "Выберите количество комнат (можно несколько):",
        options=rooms_options,
        default=rooms_options,
        key="rooms_multiselect"
    )
    

    col1, col2 = st.columns(2)
    with col1:
        exclude_first = st.checkbox("Не первый", key="exclude_first")
    with col2:
        exclude_last = st.checkbox("Не последний", key="exclude_last")
    floor_min = st.number_input("Этаж от:", min_value=1, max_value=25, value=1, key="floor_min")
    floor_max = st.number_input("Этаж до:", min_value=1, max_value=25, value=25, key="floor_max")

# === ФИЛЬТРАЦИЯ ===
filtered_df = df[
    (df['price']/1e6 >= budget_range[0]) & 
    (df['price']/1e6 <= budget_range[1]) &
    (df['reputation_score'] >= min_rating) &
    (df['year_built'] >= year_range[0]) &
    (df['year_built'] <= year_range[1])
]

if selected_housing_types:
    filtered_df = filtered_df[filtered_df['housing_type'].isin(selected_housing_types)]

if selected_rooms:
    filtered_df = filtered_df[filtered_df['rooms'].isin(selected_rooms)]

filtered_df = filtered_df[
    (filtered_df['floor'] >= floor_min) & 
    (filtered_df['floor'] <= floor_max)
]

if exclude_first:
    filtered_df = filtered_df[filtered_df['floor'] != 1]
if exclude_last:
    filtered_df = filtered_df[filtered_df['floor'] != filtered_df['total_floors']]

# === КАРТА ===
col_map, col_card = st.columns([2, 1])

with col_map:
    
    if filtered_df.empty:
        st.warning("⚠️ Нет объектов, соответствующих фильтрам")
        selected_id = None
    else:
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
                tooltip=tooltip_text
            ).add_to(m)
        
        st_folium(m, width="100%", height=500, key="map")
        
        # === ВЫБОР ТОЛЬКО ИЗ СПИСКА ===
        selected_id = None
        if not filtered_df.empty:
            options_list = ["-- Выберите объект --"] + filtered_df['short_name'].tolist()
            
            selected_option = st.selectbox(
                "Выберите объект из списка:",
                options=options_list,
                key="object_select"
            )
            
            if selected_option and selected_option != "-- Выберите объект --":
                selected_row = filtered_df[filtered_df['short_name'] == selected_option]
                if not selected_row.empty:
                    selected_id = selected_row.iloc[0]['id']
# === КАРТОЧКА ОБЪЕКТА ===
with col_card:

    
    if selected_id is not None and not filtered_df.empty:
        prop = filtered_df[filtered_df['id'] == selected_id]
        
        if not prop.empty:
            prop = prop.iloc[0]
            
            st.markdown(f"### 📍 {prop['short_name']}")
            
            price_m = prop['price'] / 1e6
            rooms = int(prop['rooms']) if pd.notna(prop['rooms']) else "н/д"
            area = prop['area'] if pd.notna(prop['area']) else "н/д"
            floor = int(prop['floor']) if pd.notna(prop['floor']) else "н/д"
            total_floors = int(prop['total_floors']) if pd.notna(prop['total_floors']) else "н/д"
            
            st.info(f"{rooms}-комн. | 📐 {area} м² | {floor}/{total_floors} эт. | 💰 {price_m:.1f} млн ₽")
            
            st.divider()
            
            col_info, col_photo = st.columns(2)
            
            with col_info:
                st.markdown("**🏗️ Общая информация**")
                st.text(f"Серия: {prop['series'] if prop['series'] else 'н/д'}")
                st.text(f"Год постройки: {int(prop['year_built']) if pd.notna(prop['year_built']) else 'н/д'}")
                st.text(f"Стены: {prop['wall_type'] if prop['wall_type'] else 'н/д'}")
                st.text(f"Метро: {prop['metro_name'] if prop['metro_name'] else 'н/д'}")
                if pd.notna(prop.get('metro_time')):
                    st.text(f"Время до метро: {prop['metro_time']} мин")
            
            with col_photo:
                st.markdown("**🖼️ Фото**")
                if prop['photo_url']:
                    try:
                        st.image(prop['photo_url'], use_container_width=True)
                    except:
                        st.image("https://placehold.co/300x200/e0e7ff/1e3a8a?text=Фото+недоступно", use_container_width=True)
                else:
                    st.image("https://placehold.co/300x200/e0e7ff/1e3a8a?text=Фото+объекта", use_container_width=True)
            
            st.divider()

            st.markdown("**🗣️ Отзывы о доме**")
            if prop['top_issues']:
                if isinstance(prop['top_issues'], str):
                    aggregated = aggregate_tags(prop['top_issues'])
                    if aggregated:
                        tags_html = render_colored_tags_with_percent(aggregated)
                        st.markdown(f"<div style='line-height:2.4;'>{tags_html}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("Нет данных об отзывах")
                elif isinstance(prop['top_issues'], list):
                    tags_string = "; ".join(prop['top_issues'])
                    aggregated = aggregate_tags(tags_string)
                    if aggregated:
                        tags_html = render_colored_tags_with_percent(aggregated)
                        st.markdown(f"<div style='line-height:2.4;'>{tags_html}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("Нет данных об отзывах")
                else:
                    st.caption("Нет данных об отзывах")
            else:
                st.caption("Нет данных об отзывах")            

           
            st.divider()
            
            st.markdown("**🏪 Инфраструктура (радиус 1 км)**")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                with col_m1:
                metro_time = int(prop['metro_time']) if pd.notna(prop['metro_time']) else None
                if metro_time:
                    dist_m = metro_time * 80
                    st.metric("🚇 До метро", f"{metro_time} мин ({dist_m} м)")
                else:
                    st.metric("🚇 До метро", "н/д")
            with col_m2:
                schools = int(prop['schools_1km']) if pd.notna(prop['schools_1km']) else "н/д"
                st.metric("🏫 Школы", schools)
            with col_m3:
                parks = int(prop['parks_1km']) if pd.notna(prop['parks_1km']) else "н/д"
                st.metric("🌲 Парки", parks)
            with col_m4:
                shops = int(prop['shops_1km']) if pd.notna(prop['shops_1km']) else "н/д"
                st.metric("🛒 Магазины", shops)
            
            st.divider()
            
            if prop.get('url'):
                st.link_button("🔗 Открыть оригинальное объявление", prop['url'], use_container_width=True)
            else:
                st.caption("Ссылка на объявление отсутствует")
        else:
            st.info("👆 Выберите объект на карте или из списка, чтобы открыть карточку.")
    else:
        st.info("👆 Выберите объект на карте или из списка, чтобы открыть карточку.")
