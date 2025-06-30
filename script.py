import google.generativeai as genai
import os
from dotenv import load_dotenv

# Загружаем переменные окружения, чтобы получить GEMINI_API_KEY
load_dotenv()

# Убедитесь, что ваш API ключ загружен
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY не найден в переменных окружения. Пожалуйста, добавьте его в ваш файл .env")

genai.configure(api_key=gemini_api_key)

print("--- Список доступных моделей Gemini ---")
found_compatible_model = False
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- **{m.name}** (поддерживает generateContent)")
        found_compatible_model = True
    else:
        print(f"- {m.name} (НЕ поддерживает generateContent)")

if not found_compatible_model:
    print("\nВНИМАНИЕ: Не найдено ни одной модели, которая бы поддерживала generateContent в вашем регионе.")
    print("Возможно, вам потребуется изменить регион или проверить настройки вашего API-ключа Gemini.")

print("--- Конец списка моделей ---")

# Теперь, когда вы получили список, вы можете прервать выполнение и изменить вашу функцию get_ai_comment
# (Если вы вставили этот код в main.py, то остальная часть кода ниже продолжит выполняться,
# но основной целью было увидеть этот вывод.)