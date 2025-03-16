# import logging
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
# import json
# import random
# import os
# import re
# from tabulate import tabulate
#
# def format_table(table_data: list) -> str:
#     if not table_data:
#         return ""
#     # Определяем порядок столбцов. Если ключи представляют собой числа в виде строк, можно отсортировать их:
#     headers = sorted(table_data[0].keys(), key=lambda x: int(x) if x.isdigit() else x)
#     # Преобразуем список словарей в список списков по порядку заголовков:
#     rows = [[str(row.get(header, "")) for header in headers] for row in table_data]
#     # Вызываем tabulate без параметра headers – тогда заголовки не выводятся.
#     table_str = tabulate(rows, tablefmt="grid", stralign="center")
#     return table_str
#
#
# def format_logical_function(text: str) -> str:
#     """
#     Ищет в тексте фрагмент, который следует после слова "выражением" в любых вариациях (например, "задается выражением" или "задаётся выражением")
#     и оборачивает только эту часть в блок <pre> для отображения в Telegram.
#
#     Если такой шаблон не найден, пытается найти вариант с "F =".
#     Если ни один из шаблонов не найден, возвращает исходный текст без изменений.
#     """
#     # Сначала пытаемся найти вариант "задается выражением" (с учетом вариаций с ё)
#     pattern_expr = re.compile(
#         r"(?:зада(?:ется|ётся)\s+выражением)\s*(.+)",
#         re.IGNORECASE | re.DOTALL
#     )
#     match_expr = pattern_expr.search(text)
#     if match_expr:
#         # Берем только то, что находится после слова "выражением"
#         func_str = match_expr.group(1).strip()
#         replacement = "\n<pre>" + func_str + "</pre>\n"
#         # Заменяем найденное вхождение на цитату (можно заменить его полностью)
#         text = pattern_expr.sub(replacement, text, count=1)
#         return text
#     else:
#         # Если не найдено, пробуем вариант "F =" (как запасной)
#         pattern_eq = re.compile(
#             r"(?:F\s*=\s*)(.+)",
#             re.IGNORECASE | re.DOTALL
#         )
#         match_eq = pattern_eq.search(text)
#         if match_eq:
#             func_str = match_eq.group(1).strip()
#             replacement = "\n<pre>" + func_str + "</pre>\n"
#             text = pattern_eq.sub(replacement, text, count=1)
#             return text
#     return text
#
#
# def clean_task_text(text: str) -> str:
#     """
#     Удаляет из текста задания блок с таблицей.
#     Эвристика:
#       - Если строка (после strip) состоит только из цифр, пробелов, символа "F" и символа "?"
#         и имеет длину менее 20 символов, то считается, что эта строка является частью таблицы.
#       - Блок таблицы — это последовательность таких строк.
#       - Остальные строки остаются без изменений.
#     """
#     lines = text.splitlines()
#     output_lines = []
#     in_table_block = False
#
#     table_line_pattern = re.compile(r"^[0-9\?\sF]+$")
#
#     for line in lines:
#         stripped = line.strip()
#         if stripped and table_line_pattern.fullmatch(stripped) and len(stripped) < 20:
#             in_table_block = True
#             continue
#         else:
#             if in_table_block:
#                 in_table_block = False
#             output_lines.append(line)
#     return "\n".join(output_lines)
#
#
# def format_function_expression(text: str) -> str:
#     """
#     Ищет в тексте фрагмент, который начинается с "F" и содержит либо "задается выражением" (или "задаётся выражением"), либо знак "=",
#     и далее – последовательность символов (буквы, цифры, скобки, пробелы, арифметические знаки, логические операторы).
#     Найденный фрагмент оборачивается в блок <pre>.
#     """
#     logical_ops = "∧∨¬→←↔∩∪≡"
#     pattern = re.compile(
#         r"(F\s*(?:зада(?:ется|ётся|ает|аёт)\s+выраж(?:ением|ением)|=)\s*[\w\(\)\s\+\-\*\/" + re.escape(
#             logical_ops) + r"]+)",
#         re.IGNORECASE
#     )
#
#     def repl(match):
#         func_str = match.group(1).strip()
#         return "\n<pre>" + func_str + "</pre>\n"
#
#     return pattern.sub(repl, text, count=1)
#
# def format_function_after_keyword(text: str) -> str:
#     """
#     Ищет в тексте фрагмент, который начинается со слова "функция" или "функции" (учитывая варианты с "задается" или с разделителями),
#     а затем следует логическая функция (с операторами, такими как ∧, ∨, ¬, →, ←, ↔, ∩, ∪, ≡ и т.п.).
#     Найденный фрагмент оборачивается в блок <pre>.
#     """
#     logical_ops = "∧∨¬→←↔∩∪≡"
#     # Ищем фразу, начинающуюся со слова "функци" (функция/функции),
#     # затем, возможно, разделитель (например, двоеточие, тире) и пробелы,
#     # затем последовательность символов, включающая буквы, цифры, скобки, пробелы, арифметические знаки и логические операторы.
#     pattern = re.compile(
#         r"((?:функци(?:я|и|ей))\s*(?:[:\-–]?\s*))([\w\(\)\s\+\-\*\/" + re.escape(logical_ops) + r"]+)",
#         re.IGNORECASE
#     )
#
#     def repl(match):
#         prefix = match.group(1)
#         expr = match.group(2).strip()
#         return prefix + "\n<pre>" + expr + "</pre>\n"
#
#     return pattern.sub(repl, text)
#
# def clean_and_format_task_text(text: str) -> str:
#     """
#     Сначала удаляет из текста блок таблицы, затем форматирует логические функции как цитаты.
#     """
#     cleaned = clean_task_text(text)
#     formatted = format_function_expression(cleaned)
#     formatted = format_function_after_keyword(formatted)
#     formatted = format_logical_function(formatted)
#     return formatted
#
#
# # Настройка базового логирования
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# # Не выводим INFO-сообщения от httpx
# logging.getLogger("httpx").setLevel(logging.WARNING)
#
# # Функция для получения пути к изображению (если изображение есть)
# def get_image_path(task_id, image_dir="images"):
#     for filename in os.listdir(image_dir):
#         if str(task_id) in filename:
#             return os.path.join(image_dir, filename)
#     return None
#
# # Функция для отправки или обновления задания
# async def send_task(query, task_number, difficulty, context):
#     # Отображаем уровень сложности в понятном виде
#     difficulty_map = {
#         "base": "Уровень: Базовый",
#         "medium": "Уровень: Средний",
#         "any": "Любой уровень"
#     }
#     difficulty_label = difficulty_map.get(difficulty, "Любой уровень")
#
#     # Загружаем задания из JSON
#     json_path = f"../parsbot/tasks_json/task_{task_number}.json"
#     with open(json_path, "r", encoding="utf-8") as file:
#         tasks_list = json.load(file)
#
#     # Фильтрация по уровню сложности (если выбран не "any")
#     if difficulty != "any":
#         tasks_list = [task for task in tasks_list if task.get('difficulty') == difficulty_label]
#
#     # Если заданий нет — сообщаем об этом
#     if not tasks_list:
#         await query.edit_message_text("Заданий с выбранным уровнем сложности не найдено.")
#         return
#
#     # Выбираем случайное задание
#     random_task = random.choice(tasks_list)
#
#     # Формируем базовый текст задания
#     task_text = random_task.get('task', 'Текст задачи отсутствует')
#     task_answer = random_task.get('answer', 'Ответ отсутствует')
#     difficulty_text = random_task.get('difficulty', 'Уровень сложности отсутствует')
#
#     response = (
#         f"Задание № {random_task['id']} ({difficulty_text}):\n\n"
#         f"{task_text}\n\n"
#         f"Ответ:<tg-spoiler> {task_answer}</tg-spoiler>"
#     )
#
#     # Применяем очистку текста, чтобы убрать лишний блок таблицы из основного описания
#     if task_number == "2":
#         response = clean_task_text(response)
#         # ...а затем выделяем логическую функцию как цитату
#         response = format_function_expression(response)
#
#     # Если задание 2 и присутствует таблица – форматируем таблицу и добавляем в текст
#     if task_number == "2" and random_task.get("table"):
#         table = random_task.get("table")
#         # Пример форматирования таблицы (здесь можно использовать tabulate или другой метод)
#         table_text = format_table(table)  # функция, которая форматирует таблицу
#         # Оборачиваем в тег <pre> для HTML-разметки:
#         response += "\n\n<b>Таблица:</b>\n<pre>" + table_text + "</pre>"
#     # Клавиатура для дальнейших действий
#     keyboard = [
#         [InlineKeyboardButton("Следующее задание", callback_data=f"difficulty_{task_number}_{difficulty}")],
#         [InlineKeyboardButton("Изменить сложность", callback_data=f"change_difficulty_{task_number}"),
#          InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     # Для заданий с изображением (например, задание 1) – отдельная логика
#     if task_number == "1":
#         # Если уже есть старое изображение, удаляем его
#         if 'current_image_message' in context.user_data:
#             try:
#                 await context.user_data['current_image_message'].delete()
#             except Exception as e:
#                 logger.error("Ошибка при удалении изображения: %s", e)
#             context.user_data.pop('current_image_message', None)
#
#         image_path = get_image_path(random_task['id'])
#         if image_path:
#             try:
#                 with open(image_path, 'rb') as img_file:
#                     image_msg = await query.message.reply_photo(
#                         photo=img_file,
#                         caption="Загрузка...",
#                         parse_mode="HTML"
#                     )
#             except Exception as e:
#                 logger.error("Ошибка при отправке изображения: %s", e)
#                 image_msg = await query.message.reply_text("Загрузка...", parse_mode="HTML")
#         else:
#             image_msg = await query.message.reply_text("Загрузка...", parse_mode="HTML")
#         context.user_data['current_image_message'] = image_msg
#
#         if 'current_text_message' in context.user_data:
#             try:
#                 await context.user_data['current_text_message'].delete()
#             except Exception as e:
#                 logger.error("Ошибка при удалении текстового сообщения: %s", e)
#             context.user_data.pop('current_text_message', None)
#
#         task_message = await query.message.reply_text(
#             text=response,
#             parse_mode="HTML",
#             reply_markup=reply_markup
#         )
#         context.user_data['current_text_message'] = task_message
#
#         if 'difficulty_message' in context.user_data:
#             try:
#                 await context.user_data['difficulty_message'].delete()
#             except Exception as e:
#                 logger.error("Ошибка при удалении сообщения с выбором сложности: %s", e)
#             context.user_data.pop('difficulty_message', None)
#
#     # Для заданий, у которых нет изображения (например, задания 2 и 8) – редактируем текущее сообщение
#     elif task_number in ["2", "8"]:
#         try:
#             task_message = await query.edit_message_text(
#                 text=response,
#                 parse_mode="HTML",
#                 reply_markup=reply_markup
#             )
#             context.user_data['current_text_message'] = task_message
#         except Exception as e:
#             logger.error("Ошибка при редактировании сообщения для задания %s: %s", task_number, e)
#         # Обновляем сохранённое сообщение выбора сложности
#         context.user_data['difficulty_message'] = task_message
#
# # Обработчик команды /start – вывод главного меню
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     keyboard = [
#         [InlineKeyboardButton("Задание 1", callback_data="task_1"),
#          InlineKeyboardButton("Задание 2", callback_data="task_2"),
#          InlineKeyboardButton("Задание 8", callback_data="task_8")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     message = await update.message.reply_text(
#         "Добро пожаловать! Выберите задание:",
#         reply_markup=reply_markup
#     )
#     context.user_data['difficulty_message'] = message
#
# # Обработчик нажатий на кнопки
# async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     query = update.callback_query
#     await query.answer()
#
#     if query.data.startswith("task_"):
#         task_number = query.data.split("_")[1]
#         context.user_data["current_task"] = task_number
#         # Создаем меню выбора сложности для выбранного задания
#         keyboard = [
#             [InlineKeyboardButton("Базовый", callback_data=f"difficulty_{task_number}_base"),
#              InlineKeyboardButton("Средний", callback_data=f"difficulty_{task_number}_medium"),
#              InlineKeyboardButton("Любой", callback_data=f"difficulty_{task_number}_any")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         message = await query.edit_message_text(
#             text=f"Выберите уровень сложности для задания {task_number}:",
#             reply_markup=reply_markup
#         )
#         context.user_data['difficulty_message'] = message
#
#     elif query.data.startswith("difficulty_"):
#         # Формат callback: difficulty_{task_number}_{difficulty}
#         _, task_number, difficulty = query.data.split("_")
#         await send_task(query, task_number, difficulty, context)
#
#     elif query.data.startswith("change_difficulty_"):
#         task_number = query.data.split("_")[2]
#         if task_number == "1" and 'current_image_message' in context.user_data:
#             try:
#                 await context.user_data['current_image_message'].delete()
#             except Exception as e:
#                 logger.error("Ошибка при удалении изображения: %s", e)
#             context.user_data.pop('current_image_message', None)
#         keyboard = [
#             [InlineKeyboardButton("Базовый", callback_data=f"difficulty_{task_number}_base"),
#              InlineKeyboardButton("Средний", callback_data=f"difficulty_{task_number}_medium"),
#              InlineKeyboardButton("Любой", callback_data=f"difficulty_{task_number}_any")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         message = await query.edit_message_text(
#             text=f"Выберите новый уровень сложности для задания {task_number}:",
#             reply_markup=reply_markup
#         )
#         context.user_data['difficulty_message'] = message
#
#     elif query.data == "back_to_menu":
#         if context.user_data.get("current_task") == "1" and 'current_image_message' in context.user_data:
#             try:
#                 await context.user_data['current_image_message'].delete()
#             except Exception as e:
#                 logger.error("Ошибка при удалении изображения: %s", e)
#             context.user_data.pop('current_image_message', None)
#         keyboard = [
#             [InlineKeyboardButton("Задание 1", callback_data="task_1"),
#              InlineKeyboardButton("Задание 2", callback_data="task_2"),
#              InlineKeyboardButton("Задание 8", callback_data="task_8")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         message = await query.edit_message_text(
#             text="Добро пожаловать! Выберите задание:",
#             reply_markup=reply_markup
#         )
#         context.user_data['difficulty_message'] = message
#
# # Основная функция
# def main() -> None:
#     # Замените "YOUR_TOKEN_HERE" на ваш токен
#     application = Application.builder().token("7716506261:AAEhZS5k-0OaEsIyZdYYJcQq2JPAK01TONM").build()
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CallbackQueryHandler(handle_callback_query))
#     application.run_polling()
#
# if __name__ == "__main__":
#     main()
