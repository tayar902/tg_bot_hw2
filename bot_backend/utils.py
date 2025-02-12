import aiohttp, requests


def calculate_water_norm(user_data):
    base_water = user_data["weight"] * 30  # Базовая норма
    activity_water = (user_data["activity"] // 30) * 500  # Вода за активность
    hot_water = 0
    if user_data["weather"] and user_data["weather"] > 25:
        hot_water = 750 # Вода за жару
    total_water = base_water + activity_water + hot_water
    return total_water

def calculate_calorie_norm(user_data):
    bmr = 10 * user_data["weight"] + 6.25 * user_data["height"] - 5 * user_data["age"]
    activity_factor = 1.2 + (user_data["activity"] / 60) * 0.1
    total_calories = bmr * activity_factor
    return int(total_calories)

async def get_weather(API_KEY, city, lang='RU', units='metric'):
    async with aiohttp.ClientSession() as session:
        lat_lon_url = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}'
        async with session.get(lat_lon_url) as lat_lon_res:
            if lat_lon_res.status != 200:
                raise Exception(await lat_lon_res.text())
            
            data = await lat_lon_res.json()
            if not data:
                raise Exception("Город не найден")

            lat = data[0]['lat']
            lon = data[0]['lon']
        
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&lang={lang}&units={units}'
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['main']['temp']
            else:
                raise Exception(await response.text())

    
async def get_food_info(product_name: str):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None
