import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Рынок жилой недвижимости Санкт-Петербурга",
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
    {"id": 1,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Кировский, Автово, м. Путиловская, улица Васи Алексеева, 14", "price": 18750000, "year_built": 1957, "reputation_score": 65, "rooms": 4, "area": 120, "floor": 1, "total_floors": 1, "series": "индивидуальный проект", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-ulica-vasi-alekseeva-2867778995-1.jpg", "top_issues": ["Хорошее расположение", "Требуется ремонт"], "dist_metro_m": 500, "schools_1km": 3, "parks_1km": 2, "shops_1km": 8},
    {"id": 2,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Калининский, Прометей, м. Гражданский проспект, Светлановский проспект, 109К1", "price": 14500000, "year_built": 1972, "reputation_score": 70, "rooms": 2, "area": 60, "floor": 4, "total_floors": 5, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-svetlanovskiy-prospekt-2886157144-1.jpg", "top_issues": ["Уютный двор", "Чистый подъезд"], "dist_metro_m": 400, "schools_1km": 4, "parks_1km": 3, "shops_1km": 12},
    {"id": 3,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Красногвардейский, Пороховые, м. Ладожская, Индустриальный проспект, 29", "price": 4750000, "year_built": 1981, "reputation_score": 55, "rooms": 2, "area": 53.0, "floor": 4, "total_floors": 16, "series": "137", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-industrialnyy-prospekt-2187124990-1.jpg", "top_issues": ["Шумновато", "Старые коммуникации"], "dist_metro_m": 600, "schools_1km": 2, "parks_1km": 1, "shops_1km": 5},
    {"id": 4,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Адмиралтейский, Адмиралтейский, м. Садовая, набережная Канала Грибоедова, 84", "price": 21566000, "year_built": 0, "reputation_score": 85, "rooms": 2, "area": 52.6, "floor": 3, "total_floors": 4, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2826664576-1.jpg", "top_issues": ["Хорошая звукоизоляция", "Светлые комнаты", "Ремонт"], "dist_metro_m": 300, "schools_1km": 5, "parks_1km": 3, "shops_1km": 15},
    {"id": 5,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Центральный, Владимирский, м. Достоевская, улица Рубинштейна, 13", "price": 17900000, "year_built": 1869, "reputation_score": 80, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-ulica-rubinshteyna-2856621331-1.jpg", "top_issues": ["Исторический центр", "Высокие потолки"], "dist_metro_m": 250, "schools_1km": 6, "parks_1km": 2, "shops_1km": 20},
    {"id": 6,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Невский, Обуховский, м. Пролетарская, улица Бабушкина, 100", "price": 7500000, "year_built": 1963, "reputation_score": 45, "rooms": 2, "area": 45.7, "floor": 3, "total_floors": 5, "series": "", "wall_type": "Панель", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2874655762-1.jpg", "top_issues": ["Шумно от соседей", "Старый лифт"], "dist_metro_m": 700, "schools_1km": 2, "parks_1km": 1, "shops_1km": 4},
    {"id": 7,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Центральный, Дворцовый, м. Гостиный двор, Большая Конюшенная улица, 25", "price": 24000000, "year_built": 1877, "reputation_score": 90, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-bolshaya-konyushennaya-ulica-2851602908-1.jpg", "top_issues": ["Элитный центр", "Двор-колодец"], "dist_metro_m": 200, "schools_1km": 7, "parks_1km": 3, "shops_1km": 25},
    {"id": 8,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Центральный, Смольнинское, м. Чернышевская, улица Восстания, 43", "price": 50000000, "year_built": 1874, "reputation_score": 95, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2891148487-1.jpg", "top_issues": ["Престижный район", "Качественная планировка"], "dist_metro_m": 150, "schools_1km": 8, "parks_1km": 4, "shops_1km": 30},
    {"id": 9,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Московский, Гагаринское, м. Московская, Бассейная улица, 63", "price": 8990000, "year_built": 1962, "reputation_score": 60, "rooms": 2, "area": 45.5, "floor": 4, "total_floors": 5, "series": "", "wall_type": "", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-basseynaya-ulica-2892562681-1.jpg", "top_issues": ["Требуется ремонт", "Старые коммуникации"], "dist_metro_m": 450, "schools_1km": 3, "parks_1km": 2, "shops_1km": 7},
    {"id": 10,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Центральный, Литейный, м. Чернышевская, улица Рылеева, 6", "price": 38900000, "year_built": 1846, "reputation_score": 92, "rooms": 2, "area": 2, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892281102-1.jpg", "top_issues": ["Исторический центр", "Дорого и качественно"], "dist_metro_m": 180, "schools_1km": 6, "parks_1km": 3, "shops_1km": 22},
    {"id": 11,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Петроградский, Кронверкское, м. Горьковская, Сытнинская площадь, 3", "price": 41500000, "year_built": 1877, "reputation_score": 88, "rooms": 2, "area": 104.0, "floor": 3, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2820229159-1.jpg", "top_issues": ["Просторные комнаты", "Центр города"], "dist_metro_m": 350, "schools_1km": 5, "parks_1km": 3, "shops_1km": 18},
    {"id": 12,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Красногвардейский, Малая Охта, м. Новочеркасская, проспект Шаумяна, 67", "price": 7750000, "year_built": 1960, "reputation_score": 50, "rooms": 2, "area": 45.8, "floor": 3, "total_floors": 5, "series": "1-335", "wall_type": "Панель", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892505528-1.jpg", "top_issues": ["Бюджетный вариант", "Требуется ремонт"], "dist_metro_m": 550, "schools_1km": 2, "parks_1km": 1, "shops_1km": 4},
    {"id": 13,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Адмиралтейский, Коломна, м. Балтийская, набережная Реки Фонтанки, 179", "price": 17700000, "year_built": 1912, "reputation_score": 78, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-naberezhnaya-reki-fontanki-2880781431-1.jpg", "top_issues": ["Вид на Фонтанку", "Исторический центр"], "dist_metro_m": 400, "schools_1km": 4, "parks_1km": 2, "shops_1km": 12},
    {"id": 14,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Фрунзенский, Волковское, м. Волковская, Волковский проспект, 14", "price": 9000000, "year_built": 1917, "reputation_score": 58, "rooms": 2, "area": 51.5, "floor": 4, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-volkovskiy-prospekt-2864927880-1.jpg", "top_issues": ["Старый фонд", "Хорошая планировка"], "dist_metro_m": 480, "schools_1km": 3, "parks_1km": 2, "shops_1km": 6},
    {"id": 15,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Невский, Народный, м. Ломоносовская, проспект Большевиков, 59К1", "price": 7100000, "year_built": 1963, "reputation_score": 48, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "од-6", "wall_type": "", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892370398-1.jpg", "top_issues": ["Дешево", "Недалеко от метро"], "dist_metro_m": 650, "schools_1km": 2, "parks_1km": 1, "shops_1km": 5},
    {"id": 16,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Приморский, Юнтолово, м. Комендантский проспект, проспект Королева, 54К1", "price": 15550000, "year_built": 1989, "reputation_score": 72, "rooms": 2, "area": 45.8, "floor": 4, "total_floors": 9, "series": "1лг-504", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2887193881-1.jpg", "top_issues": ["Новостройка", "Развитая инфраструктура"], "dist_metro_m": 300, "schools_1km": 4, "parks_1km": 3, "shops_1km": 10},
    {"id": 17,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Центральный, № 78, м. Сенная площадь, набережная Реки Фонтанки, 73", "price": 31000000, "year_built": 1828, "reputation_score": 86, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892920324-1.jpg", "top_issues": ["Центр", "Вид на Фонтанку"], "dist_metro_m": 280, "schools_1km": 6, "parks_1km": 3, "shops_1km": 20},
    {"id": 18,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Приморский, Чёрная речка, м. Черная речка, Лисичанская улица, 8", "price": 8500000, "year_built": 1899, "reputation_score": 62, "rooms": 2, "area": 39.7, "floor": 5, "total_floors": 6, "series": "", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-lisichanskaya-ulica-2853417402-1.jpg", "top_issues": ["Дореволюционный дом", "Высокие потолки"], "dist_metro_m": 380, "schools_1km": 3, "parks_1km": 2, "shops_1km": 8},
    {"id": 19,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Петроградский, Посадский, м. Горьковская, Мичуринская улица, 1", "price": 32900000, "year_built": 1951, "reputation_score": 83, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2872319947-1.jpg", "top_issues": ["Сталинский дом", "Петроградская сторона"], "dist_metro_m": 320, "schools_1km": 5, "parks_1km": 4, "shops_1km": 15},
    {"id": 20,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Петроградский, Посадский, м. Горьковская, улица Куйбышева, 1/5", "price": 26900000, "year_built": 1955, "reputation_score": 80, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2871870239-1.jpg", "top_issues": ["Сталинка", "Хорошая планировка"], "dist_metro_m": 340, "schools_1km": 5, "parks_1km": 3, "shops_1km": 16},
    {"id": 21,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Невский, Правобережный, м. Проспект Большевиков, улица Ворошилова, 1", "price": 10990000, "year_built": 1995, "reputation_score": 75, "rooms": 2, "area": 65.3, "floor": 4, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892405402-1.jpg", "top_issues": ["Относительно новый дом", "Просторные комнаты"], "dist_metro_m": 420, "schools_1km": 3, "parks_1km": 2, "shops_1km": 9},
    {"id": 22,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Калининский, Финляндский, м. Выборгская, Кондратьевский проспект, 32", "price": 9999999, "year_built": 1904, "reputation_score": 65, "rooms": 2, "area": 64.4, "floor": 2, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2840472221-1.jpg", "top_issues": ["Дореволюционный", "Требуется ремонт"], "dist_metro_m": 480, "schools_1km": 3, "parks_1km": 2, "shops_1km": 10},
    {"id": 23,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Невский, Невская застава, м. Елизаровская, улица Бабушкина, 31", "price": 9250000, "year_built": 1961, "reputation_score": 52, "rooms": 2, "area": 40.9, "floor": 2, "total_floors": 5, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2837867466-1.jpg", "top_issues": ["Хрущевка", "Маленькая кухня"], "dist_metro_m": 580, "schools_1km": 2, "parks_1km": 1, "shops_1km": 6},
    {"id": 24,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Калининский, Академическое, м. Политехническая, Тихорецкий проспект, 33К2", "price": 8500000, "year_built": 1977, "reputation_score": 55, "rooms": 2, "area": 49.2, "floor": 11, "total_floors": 12, "series": "1лг-504", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-tihoreckiy-prospekt-2889092254-1.jpg", "top_issues": ["Чистый подъезд", "Требуется ремонт"], "dist_metro_m": 350, "schools_1km": 4, "parks_1km": 3, "shops_1km": 9},
    {"id": 25,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Центральный, Дворцовый, м. Гостиный двор, Итальянская улица, 12Ж", "price": 42900000, "year_built": 1917, "reputation_score": 91, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-italyanskaya-ulica-2839906651-1.jpg", "top_issues": ["Элитное жилье", "Сердце города"], "dist_metro_m": 150, "schools_1km": 7, "parks_1km": 3, "shops_1km": 28},
    {"id": 26,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Центральный, Владимирский, м. Маяковская, Поварской переулок, 14", "price": 36000000, "year_built": 1879, "reputation_score": 87, "rooms": 2, "area": 104.0, "floor": 3, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892462179-1.jpg", "top_issues": ["Огромная площадь", "Высокий потолок"], "dist_metro_m": 220, "schools_1km": 5, "parks_1km": 2, "shops_1km": 18},
    {"id": 27,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Невский, № 54, м. Улица Дыбенко, улица Шотмана, 12К1", "price": 8200000, "year_built": 1969, "reputation_score": 48, "rooms": 2, "area": 44.5, "floor": 5, "total_floors": 9, "series": "", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892976951-1.jpg", "top_issues": ["Шумновато", "Старый лифт"], "dist_metro_m": 400, "schools_1km": 2, "parks_1km": 1, "shops_1km": 5},
    {"id": 28,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Василеостровский, № 7, м. Василеостровская, проспект Большой Васильевского острова, 26", "price": 29056000, "year_built": 0, "reputation_score": 82, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2684501290-1.jpg", "top_issues": ["Василеостровский район", "Хорошее расположение"], "dist_metro_m": 300, "schools_1km": 5, "parks_1km": 3, "shops_1km": 14},
    {"id": 29,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Фрунзенский, Георгиевский, м. Проспект Славы, проспект Славы, 35К1", "price": 9950000, "year_built": 1967, "reputation_score": 54, "rooms": 2, "area": 44.0, "floor": 5, "total_floors": 9, "series": "", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2890868121-1.jpg", "top_issues": ["Старые коммуникации", "Требуется ремонт"], "dist_metro_m": 380, "schools_1km": 3, "parks_1km": 2, "shops_1km": 7},
    {"id": 30,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Приморский, Чёрная речка, м. Черная речка, Школьная улица, 6", "price": 10600000, "year_built": 1960, "reputation_score": 60, "rooms": 2, "area": 43.3, "floor": 3, "total_floors": 5, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-shkolnaya-ulica-2886666953-1.jpg", "top_issues": ["Близко к метро", "Хорошее расположение"], "dist_metro_m": 280, "schools_1km": 3, "parks_1km": 2, "shops_1km": 9},
    {"id": 31,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Красносельский, Южно-Приморский, м. Юго-Западная, Петергофское шоссе, 21К1", "price": 7800000, "year_built": 1979, "reputation_score": 45, "rooms": 2, "area": 44.0, "floor": 4, "total_floors": 9, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2888244917-1.jpg", "top_issues": ["Шумная улица", "Требуется ремонт"], "dist_metro_m": 500, "schools_1km": 2, "parks_1km": 1, "shops_1km": 5},
    {"id": 32,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Калининский, Гражданка, м. Академическая, проспект Науки, 45К2", "price": 9000000, "year_built": 1972, "reputation_score": 52, "rooms": 2, "area": 47.0, "floor": 6, "total_floors": 9, "series": "", "wall_type": "Панель", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2886887224-1.jpg", "top_issues": ["Требуется ремонт", "Недалеко от метро"], "dist_metro_m": 350, "schools_1km": 4, "parks_1km": 2, "shops_1km": 8},
    {"id": 33,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Кировский, Нарвский, м. Нарвская, проспект Стачек, 19", "price": 11000000, "year_built": 1951, "reputation_score": 68, "rooms": 2, "area": 56.6, "floor": 3, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2736742671-1.jpg", "top_issues": ["Сталинский дом", "Большие комнаты"], "dist_metro_m": 250, "schools_1km": 4, "parks_1km": 2, "shops_1km": 12},
    {"id": 34,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Калининский, № 21, м. Гражданский проспект, проспект Просвещения, 87К1", "price": 11900000, "year_built": 1983, "reputation_score": 65, "rooms": 2, "area": 53.5, "floor": 7, "total_floors": 13, "series": "индивидуальный проект", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2883484553-1.jpg", "top_issues": ["Хорошая планировка", "Развитая инфраструктура"], "dist_metro_m": 300, "schools_1km": 4, "parks_1km": 3, "shops_1km": 11},
    {"id": 35,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Московский, Пулковский меридиан, м. Московская, Московский проспект, 205", "price": 9990000, "year_built": 1963, "reputation_score": 58, "rooms": 2, "area": 43.54, "floor": 4, "total_floors": 9, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2852422603-1.jpg", "top_issues": ["Хороший район", "Требуется ремонт"], "dist_metro_m": 400, "schools_1km": 3, "parks_1km": 2, "shops_1km": 8},
    {"id": 36,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Кировский, Дачное, м. Ленинский проспект, улица Зины Портновой, 11", "price": 9700000, "year_built": 1965, "reputation_score": 55, "rooms": 2, "area": 45.0, "floor": 2, "total_floors": 9, "series": "", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-sanktpeterburg-ulica-ziny-portnovoy-2891492724-1.jpg", "top_issues": ["Старые коммуникации", "Недалеко от метро"], "dist_metro_m": 320, "schools_1km": 3, "parks_1km": 2, "shops_1km": 7},
    {"id": 37,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Калининский, Северный, м. Проспект Просвещения, проспект Культуры, 19", "price": 9400000, "year_built": 0, "reputation_score": 50, "rooms": 2, "area": 51.7, "floor": 11, "total_floors": 16, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2849724255-1.jpg", "top_issues": ["Требуется ремонт", "Близко к метро"], "dist_metro_m": 280, "schools_1km": 4, "parks_1km": 2, "shops_1km": 10},
    {"id": 38,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Центральный, Литейный, м. Чернышевская, Моховая улица, 5", "price": 21850000, "year_built": 1798, "reputation_score": 85, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2877715405-1.jpg", "top_issues": ["Очень старый дом", "Историческая ценность"], "dist_metro_m": 200, "schools_1km": 6, "parks_1km": 3, "shops_1km": 20},
    {"id": 39,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Пушкинский, мкр. Пушкин, м. Купчино, Октябрьский бульвар, 22а", "price": 7500000, "year_built": 1959, "reputation_score": 42, "rooms": 2, "area": 40.0, "floor": 2, "total_floors": 3, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-pushkin-oktyabrskiy-bulvar-2879560516-1.jpg", "top_issues": ["Далеко от центра", "Требуется ремонт"], "dist_metro_m": 800, "schools_1km": 2, "parks_1km": 1, "shops_1km": 4},
    {"id": 40,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Выборгский, № 15, м. Проспект Просвещения, улица Кустодиева, 12", "price": 10000000, "year_built": 1974, "reputation_score": 56, "rooms": 2, "area": 44.6, "floor": 5, "total_floors": 9, "series": "", "wall_type": "", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2886319043-1.jpg", "top_issues": ["Хорошая транспортная доступность"], "dist_metro_m": 350, "schools_1km": 4, "parks_1km": 2, "shops_1km": 9},
    {"id": 41,"housing_type": "Вторичка","address": "Санкт-Петербург, р-н Невский, Рыбацкое, м. Рыбацкое, Прибрежная улица, 4", "price": 12500000, "year_built": 1997, "reputation_score": 74, "rooms": 2, "area": 0, "floor": 0, "total_floors": 0, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": True, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2848737997-1.jpg", "top_issues": ["Относительно новый", "Хорошее расположение"], "dist_metro_m": 400, "schools_1km": 3, "parks_1km": 2, "shops_1km": 7},
    {"id": 42,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Выборгский, Светлановское, м. Удельная, Манчестерская улица, 6", "price": 12990000, "year_built": 1969, "reputation_score": 62, "rooms": 2, "area": 49.9, "floor": 4, "total_floors": 12, "series": "", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2892552691-1.jpg", "top_issues": ["Недалеко от метро", "Тихий район"], "dist_metro_m": 450, "schools_1km": 4, "parks_1km": 2, "shops_1km": 8},
    {"id": 43,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Выборгский, Шувалово-Озерки, м. Проспект Просвещения, Суздальский проспект, 1к1", "price": 9500000, "year_built": 1986, "reputation_score": 52, "rooms": 2, "area": 55.5, "floor": 10, "total_floors": 12, "series": "137", "wall_type": "Панель", "has_lift": True, "has_balcony": True, "photo_url": "https://images.cdn-cian.ru/images/2864766353-1.jpg", "top_issues": ["Старые коммуникации", "Требуется ремонт"], "dist_metro_m": 380, "schools_1km": 3, "parks_1km": 2, "shops_1km": 9},
    {"id": 44,"housing_type": "Вторичка", "address": "Санкт-Петербург, р-н Фрунзенский, Волковское, м. Обводный канал, Боровая улица, 94", "price": 13490000, "year_built": 1917, "reputation_score": 70, "rooms": 2, "area": 80.0, "floor": 4, "total_floors": 5, "series": "индивидуальный проект", "wall_type": "Кирпич", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/2768396432-1.jpg", "top_issues": ["Большая площадь", "Дореволюционный"], "dist_metro_m": 350, "schools_1km": 3, "parks_1km": 2, "shops_1km": 10},
    {"id": 45, "housing_type": "Вторичка","address": "Санкт-Петербург, р-н Пушкинский, мкр. Пушкин, м. Московская, Лесное тер., 1", "price": 5130000, "year_built": 1971, "reputation_score": 38, "rooms": 2, "area": 44.8, "floor": 3, "total_floors": 5, "series": "", "wall_type": "Панель", "has_lift": False, "has_balcony": False, "photo_url": "https://images.cdn-cian.ru/images/kvartira-lesnoe-2548517187-1.jpg", "top_issues": ["Далеко от центра", "Дешево"], "dist_metro_m": 900, "schools_1km": 2, "parks_1km": 1, "shops_1km": 3},
]

# === ОБРАБОТКА ДАННЫХ ===
for building in buildings_data:
    lat, lon = get_coords_from_address(building["address"])
    building["lat"] = lat
    building["lon"] = lon
	
    if building["id"] == 43:
        building["lat"] = 60.066549
        building["lon"] = 30.303741
    
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
st.title("Рынок жилой недвижимости Санкт-Петербурга")
st.caption("Прототип аналитической системы | ФКТИ СПбГЭТУ «ЛЭТИ» | 2026")

# === БОКОВАЯ ПАНЕЛЬ ===
with st.sidebar:
    st.header("Фильтры")
    
    min_rating = st.slider("Мин. рейтинг репутации 🛈", 0, 100, 0, key="rating")
    st.subheader("Тип жилья")
    selected_housing_types = st.multiselect(
        "Выберите тип жилья (можно несколько):",
        options=["Новостройка", "Вторичка"],
        default=["Новостройка", "Вторичка"],
        key="housing_multiselect"
    )
	
    min_price = float(df['price'].min())
    max_price = float(df['price'].max())
    budget_range = st.slider("Бюджет (млн ₽)", min_price/1e6, max_price/1e6, (min_price/1e6, max_price/1e6), key="budget")
    
    st.subheader("Год постройки")
    min_year = int(df['year_built'].min()) if df['year_built'].min() > 0 else 1900
    max_year = int(df['year_built'].max()) if df['year_built'].max() > 0 else 2024
    year_range = st.slider(
        "Выберите диапазон годов:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        key="year_range"
    )
    

    st.subheader("Количество комнат")
    selected_rooms = st.multiselect(
        "Выберите количество комнат (можно несколько):",
        options=[1, 2, 3, 4, 5],
        default=[1, 2, 3, 4, 5],
        key="rooms_multiselect"
    )

    st.subheader("Этаж")
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
    (df['reputation_score'] >= min_rating)
]

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

filtered_df = df[
    (df['price']/1e6 >= budget_range[0]) & 
    (df['price']/1e6 <= budget_range[1]) &
    (df['reputation_score'] >= min_rating) &
    (df['year_built'] >= year_range[0]) &
    (df['year_built'] <= year_range[1])
]

# Фильтр по типу жилья
if selected_housing_types:
    filtered_df = filtered_df[filtered_df['housing_type'].isin(selected_housing_types)]
# === КАРТА ===
col_map, col_card = st.columns([2, 1])

with col_map:
    
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

