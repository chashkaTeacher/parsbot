# utils.py
import os


import os

def get_image_path(task_number, task):
    """
    Получает путь к первому изображению из JSON в формате:
    tasks_json/task_{номер}/images/{имя_файла}.png
    """
    images = task.get("images", [])

    if not images:
        return None  # Нет изображений в JSON

    # Берём первое изображение (оно уже содержит только имя файла, например "10009_10009.png")
    image_filename = os.path.basename(images[0])  # Убираем лишние пути, если они есть

    # Формируем правильный путь
    image_path = os.path.join("tasks_json", f"task_{task_number}", "images", image_filename)

    # Проверяем, существует ли файл
    if os.path.exists(image_path):
        return image_path
    else:
        print(f"⚠ Изображение не найдено: {image_path}")
        return None


