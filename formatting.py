# formatting.py
import re
from tabulate import tabulate


def format_table(table_data: list) -> str:
    if not table_data:
        return ""
    # Определяем порядок столбцов. Если ключи представляют собой числа в виде строк, можно отсортировать их:
    headers = sorted(table_data[0].keys(), key=lambda x: int(x) if x.isdigit() else x)
    # Преобразуем список словарей в список списков по порядку заголовков:
    rows = [[str(row.get(header, "")) for header in headers] for row in table_data]
    # Вызываем tabulate без параметра headers – тогда заголовки не выводятся.
    table_str = tabulate(rows, tablefmt="grid", stralign="center")
    return table_str

def clean_task_text(text: str) -> str:
    """
    Очищает текст задачи:
    1. Удаляет блоки таблицы (если их не нужно хранить отдельно).
    2. Убирает лишние переносы строк в предложениях.
    3. Сохраняет переносы перед таблицами и ключевыми словами.
    4. **Оставляет строку "Ответ:" на новой строке**
    """

    lines = text.splitlines()
    output_lines = []
    in_table_block = False

    # Регулярное выражение для строк таблицы (цифры, пробелы, F, ?)
    table_line_pattern = re.compile(r"^[0-9\?\sF]+$")

    for line in lines:
        stripped = line.strip()

        # Если строка похожа на таблицу — пропускаем её
        if stripped and table_line_pattern.fullmatch(stripped) and len(stripped) < 20:
            in_table_block = True
            continue
        else:
            if in_table_block:
                in_table_block = False
            output_lines.append(line)

    cleaned_text = "\n".join(output_lines)

    # Удаление лишних переносов перед таблицей
    cleaned_text = re.sub(r"\n+(\?[\s\?F\d]+)", r"\n\1", cleaned_text)

    # Удаление лишних переносов перед ключевыми фразами ("Определите", "В ответе напишите" и т.д.)
    cleaned_text = re.sub(r"\n+(Определите|В ответе напишите)", r"\n\1", cleaned_text)

    # Удаление лишних переносов строк, **если текст продолжается в том же предложении**,
    # но с исключением "Ответ:", который должен оставаться на новой строке
    cleaned_text = re.sub(r"(?<!\.)\n(?!\n|Ответ:)", " ", cleaned_text)

    # Гарантируем, что **"Ответ:" всегда с новой строки**
    cleaned_text = re.sub(r"(\S)\s*(Ответ:)", r"\1\n\n\2", cleaned_text)

    # Удаление повторных пробелов
    cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)

    return cleaned_text.strip()




def format_logical_expression(text: str) -> str:
    """
    Находит и форматирует логическое выражение в тексте, заменяя его на <pre>...</pre>.
    Учитывает:
    - Все возможные формы слов "функция", "выражение", "формула".
    - Наличие двоеточия `:` после "выражением".
    - Корректное завершение формулы без выделения лишних частей (например, одиночной `F`).
    """

    # 🔥 Логические операторы
    logical_ops = "∧∨¬→←↔∩∪≡⊕⇔⊙⊤⊥"

    # 🛠 Универсальный паттерн для поиска логической функции
    pattern = re.compile(
        r"(\b(?:функци(?:я|и|ей|ю|ям|ями|ях)|выражени(?:е|я|ем|ю|и|ям|ями|ях)|формул(?:а|ой|ы|е|у|ами|ах))\s*:?\s*)"  # "Функция", "выражение" или "формула" + двоеточие (если есть)
        r"([^\n]+?)"  # 🛠 Само выражение (все символы до следующего ограничителя)
        r"\s*(?:но\s+успел|на\s+рисунке|которая\s+определяет|определите|содержит|изображен(?:ный|ная)|[,.])",  # Ограничители после выражения
        re.IGNORECASE | re.DOTALL
    )

    def repl(match):
        prefix = match.group(1)  # Слово "функция", "выражение" или "формула"
        expr = match.group(2).strip()  # Логическое выражение

        # Проверяем, не содержит ли выражение только "F" без логических операторов
        if expr.strip().upper() == "F":
            return match.group(0)  # Оставляем текст как есть, не выделяем "F"

        return f"{prefix}<pre>{expr}</pre>"

    return pattern.sub(repl, text, count=1)




def clean_and_format_task_text(text: str) -> str:
    """
    Удаляет лишнюю таблицу и форматирует логическое выражение в <pre> ... </pre>.
    """
    cleaned = clean_task_text(text)
    formatted = format_logical_expression(cleaned)
    return formatted


