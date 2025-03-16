import json

# Путь к JSON-файлу
json_file_path = "tasks_json/task_22/task_22.json"

# Читаем JSON-файл
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

updated = False  # Флаг, указывающий, были ли изменения

# Проходим по всем записям в файле
for entry in data:
    if "table" in entry and isinstance(entry["table"], list) and len(entry["table"]) > 0:
        # Проверяем, что первая строка таблицы содержит нужные заголовки
        first_row = entry["table"][0]
        print(f"Проверяем запись: {first_row}")

        # Приводим к единому формату для сравнения
        first_row_cleaned = {
            key: value.replace("(-ов)", "(ов)").replace("A", "А").strip()
            for key, value in first_row.items()
        }

        if (
            "0" in first_row_cleaned and first_row_cleaned["0"] == "ID процесса B" and
            "1" in first_row_cleaned and first_row_cleaned["1"] == "Время выполнения процесса B (мс)" and
            "2" in first_row_cleaned and first_row_cleaned["2"] == "ID процесса(ов) А"
        ):
            # ✅ Заменяем заголовки
            entry["table"][0] = {
                "0": "ID B",
                "1": "время B (мс)",
                "2": "ID A"
            }
            updated = True
            print("✅ Заголовки успешно обновлены!")

# Сохраняем обновленный JSON обратно в файл, если были изменения
if updated:
    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print("✅ Файл успешно обновлен!")
else:
    print("⚠ Изменений не было, файл остался без изменений.")
