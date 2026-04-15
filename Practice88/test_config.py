from config import load_config

try:
    config = load_config()
    print("Конфигурация загружена успешно!")
    print(config)
except Exception as e:
    print(f"Ошибка: {e}")