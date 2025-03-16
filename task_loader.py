# task_loader.py
import json
import os
import random
from config import JSON_DIR

def load_tasks(task_number: str, difficulty: str) -> list:
    """
    Загружает задачи для указанного номера задачи из JSON-файла в формате:
    tasks_json/task_{номер}/task_{номер}.json
    """
    file_path = os.path.join(JSON_DIR, f"task_{task_number}", f"task_{task_number}.json")

    if not os.path.exists(file_path):
        print(f"⚠ Файл с заданиями не найден: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    if difficulty.lower() != "any":
        diff_val = {"base": "Уровень: Базовый", "medium": "Уровень: Средний"}.get(difficulty.lower(), "")
        tasks = [task for task in tasks if task.get("difficulty", "").strip() == diff_val]

    return tasks

def get_random_task(task_number: str, difficulty: str) -> dict:
    """
    Возвращает случайное задание из JSON-файла внутри папки своей задачи.
    """
    tasks = load_tasks(task_number, difficulty)
    if not tasks:
        return {}
    return random.choice(tasks)
