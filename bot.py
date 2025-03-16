# bot.py
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN  # должен содержать BOT_TOKEN, JSON_DIR, IMAGES_DIR и т.д.
from task_loader import get_random_task
from formatting import clean_and_format_task_text, format_table
from utils import get_image_path
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)




async def start(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None, force_run: bool = False) -> None:
    """Обработчик команды /start, очищает старые файлы и сообщения при запуске бота."""
    logger.info("🚀 Бот перезапущен! Удаляем старые файлы и сообщения...")

    # Если update и context нет (бот только что запущен), используем сохранённый chat_id
    chat_id = update.message.chat_id if update else context.bot_data.get('chat_id')

    if not chat_id:
        logger.info("⚠ chat_id не найден, команда /start не может быть выполнена.")
        return

    context.bot_data['chat_id'] = chat_id  # Сохраняем chat_id

    keyboard = [
        [InlineKeyboardButton("Задание 1", callback_data="task_1"),
         InlineKeyboardButton("Задание 2", callback_data="task_2"),
         InlineKeyboardButton("Задание 3", callback_data="task_3")],
        [InlineKeyboardButton("Задание 4", callback_data="task_4"),
         InlineKeyboardButton("Задание 8", callback_data="task_8"),
         InlineKeyboardButton("Задание 9", callback_data="task_9")],
        [InlineKeyboardButton("Задание 17", callback_data="task_17"),
         InlineKeyboardButton("Задание 22", callback_data="task_22"),
         InlineKeyboardButton("Задание 27", callback_data="task_27")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(chat_id=chat_id, text="Добро пожаловать! Выберите задание:", reply_markup=reply_markup)

    # Логируем сообщение, которое добавляется в список
    logger.info(f"📌 Новое сообщение добавлено в список удаления: {message.message_id}")

    # Сохраняем ID сообщений, чтобы их удалить при следующем запуске
    context.bot_data.setdefault('message_ids', []).append(message.message_id)


async def display_task(query: Update, task_number: str, difficulty: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = get_random_task(task_number, difficulty)
    if not task:
        await query.edit_message_text("Заданий с выбранным уровнем сложности не найдено.")
        return

    task_text = task.get('task', 'Текст задачи отсутствует')
    task_answer = task.get('answer', 'Ответ отсутствует')
    diff_text = task.get('difficulty', 'Уровень сложности отсутствует')

    # ✅ Форматируем текст задачи
    formatted_task_text = clean_and_format_task_text(task_text)

    raw_response = (
        f"Задание № <code>{task.get('id', 'N/A')}</code> ({diff_text}):\n\n"
        f"{formatted_task_text}\n\n"
        f"Ответ:<tg-spoiler> {task_answer}</tg-spoiler>"
    )

    if task.get("table"):
        table_text = format_table(task.get("table"))
        raw_response += "\n\n<b>Таблица:</b>\n<pre>" + table_text + "</pre>"

    formatted_text = raw_response

    keyboard = [
        [InlineKeyboardButton("Следующее задание", callback_data=f"difficulty_{task_number}_{difficulty}")],
        [InlineKeyboardButton("Изменить сложность", callback_data=f"change_difficulty_{task_number}"),
         InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 🖼 **Обработка изображений (если есть)**
    images = task.get("images", [])
    image_path = get_image_path(task_number, task) if images else None
    has_image = bool(image_path)

    # 📂 **Обработка файлов (если есть)**
    file_paths = [os.path.normpath(fp) for fp in task.get("files", []) if os.path.exists(fp)]
    has_files = bool(file_paths)

    # 🗑 **Удаление старых сообщений, если в JSON есть файлы или изображения**
    if has_files or has_image:
        if 'current_file_messages' in context.user_data:
            for file_msg in context.user_data['current_file_messages']:
                try:
                    await file_msg.delete()
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла: {e}")
            context.user_data.pop('current_file_messages', None)

        if 'current_image_message' in context.user_data:
            try:
                await context.user_data['current_image_message'].delete()
            except Exception as e:
                logger.error("Ошибка при удалении изображения: %s", e)
            context.user_data.pop('current_image_message', None)

        if 'current_text_message' in context.user_data:
            try:
                await context.user_data['current_text_message'].delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении текстового сообщения: {e}")
            context.user_data.pop('current_text_message', None)

    # 📝 **Редактируем текст, если нет изображений и файлов**
    elif 'current_text_message' in context.user_data:
        try:
            await context.user_data['current_text_message'].edit_text(
                text=formatted_text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            logger.info("Текстовое сообщение обновлено.")
            return  # Завершаем выполнение, так как текст уже обновлён
        except Exception as e:
            logger.error(f"Ошибка при редактировании текста задания: {e}")

    # 🖼 **Отправка изображения, если есть**
    if image_path:
        try:
            with open(image_path, 'rb') as img_file:
                image_msg = await query.message.reply_photo(
                    photo=img_file,
                    caption="Задание с изображением:",
                    parse_mode="HTML"
                )
            logger.info(f"Изображение {image_path} успешно отправлено.")
            context.user_data['current_image_message'] = image_msg
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения {image_path}: {e}")
            await query.message.reply_text("Ошибка загрузки изображения.", parse_mode="HTML")

    # 📂 **Отправка файлов перед текстом, если нет изображения**
    file_messages = []
    if has_files and not has_image:
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            try:
                doc_msg = await query.message.reply_document(
                    document=open(file_path, 'rb'),
                    caption=f"📄 {file_name} (нажмите, чтобы скачать)"
                )
                file_messages.append(doc_msg)
                logger.info(f"Файл {file_path} успешно отправлен.")
            except Exception as e:
                logger.error(f"Ошибка при отправке файла {file_path}: {e}")

        context.user_data['current_file_messages'] = file_messages

    # 📝 **Отправка нового текста, если не было редактирования**
    task_message = await query.message.reply_text(
        text=formatted_text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    context.user_data['current_text_message'] = task_message
    logger.info("Текстовое сообщение отправлено.")

    # 📂 **Отправка файлов после текста, если было изображение**
    if has_files and has_image:
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            try:
                doc_msg = await query.message.reply_document(
                    document=open(file_path, 'rb'),
                    caption=f"📄 {file_name} (нажмите, чтобы скачать)"
                )
                file_messages.append(doc_msg)
                logger.info(f"Файл {file_path} успешно отправлен.")
            except Exception as e:
                logger.error(f"Ошибка при отправке файла {file_path}: {e}")

        context.user_data['current_file_messages'] = file_messages

    # 🗑 **Удаление старого сообщения с выбором сложности**
    if 'difficulty_message' in context.user_data:
        try:
            await context.user_data['difficulty_message'].delete()
        except Exception as e:
            logger.error("Ошибка при удалении сообщения с выбором сложности: %s", e)
        context.user_data.pop('difficulty_message', None)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("task_"):
        task_number = data.split("_")[1]
        context.user_data["current_task"] = task_number
        keyboard = [
            [InlineKeyboardButton("Базовый", callback_data=f"difficulty_{task_number}_base"),
             InlineKeyboardButton("Средний", callback_data=f"difficulty_{task_number}_medium"),
             InlineKeyboardButton("Любой", callback_data=f"difficulty_{task_number}_any")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await query.edit_message_text(
            text=f"Выберите уровень сложности для задания {task_number}:",
            reply_markup=reply_markup
        )
        context.user_data['difficulty_message'] = message

    elif data.startswith("difficulty_"):
        parts = data.split("_")
        if len(parts) >= 3:
            _, task_number, difficulty = parts
            await display_task(query, task_number, difficulty, context)
        else:
            await query.edit_message_text("Некорректные данные.")

    elif data.startswith("change_difficulty_"):
        task_number = data.split("_")[2]

        # 🗑 **Удаление всех файлов перед изменением сложности**
        if 'current_file_messages' in context.user_data:
            for file_msg in context.user_data['current_file_messages']:
                try:
                    await file_msg.delete()
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла: {e}")
            context.user_data.pop('current_file_messages', None)

        # 🗑 **Удаление изображения перед изменением сложности**
        if 'current_image_message' in context.user_data:
            try:
                await context.user_data['current_image_message'].delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении изображения: {e}")
            context.user_data.pop('current_image_message', None)

        keyboard = [
            [InlineKeyboardButton("Базовый", callback_data=f"difficulty_{task_number}_base"),
             InlineKeyboardButton("Средний", callback_data=f"difficulty_{task_number}_medium"),
             InlineKeyboardButton("Любой", callback_data=f"difficulty_{task_number}_any")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await query.edit_message_text(
            text=f"Выберите новый уровень сложности для задания {task_number}:",
            reply_markup=reply_markup
        )
        context.user_data['difficulty_message'] = message

    elif data == "back_to_menu":
        # 🗑 **Удаление всех файлов перед возвратом в меню**
        if 'current_file_messages' in context.user_data:
            for file_msg in context.user_data['current_file_messages']:
                try:
                    await file_msg.delete()
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла: {e}")
            context.user_data.pop('current_file_messages', None)

        # 🗑 **Удаление изображения перед возвратом в меню**
        if 'current_image_message' in context.user_data:
            try:
                await context.user_data['current_image_message'].delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении изображения: {e}")
            context.user_data.pop('current_image_message', None)

        keyboard = [
            [InlineKeyboardButton("Задание 1", callback_data="task_1"),
             InlineKeyboardButton("Задание 2", callback_data="task_2"),
             InlineKeyboardButton("Задание 3", callback_data="task_3")],
            [InlineKeyboardButton("Задание 4", callback_data="task_4"),
             InlineKeyboardButton("Задание 8", callback_data="task_8"),
             InlineKeyboardButton("Задание 9", callback_data="task_9")],
            [InlineKeyboardButton("Задание 17", callback_data="task_17"),
             InlineKeyboardButton("Задание 22", callback_data="task_22"),
             InlineKeyboardButton("Задание 27", callback_data="task_27")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await query.edit_message_text(
            text="Добро пожаловать! Выберите задание:",
            reply_markup=reply_markup
        )
        context.user_data['difficulty_message'] = message



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Задание 1", callback_data="task_1"),
         InlineKeyboardButton("Задание 2", callback_data="task_2"),
         InlineKeyboardButton("Задание 3", callback_data="task_3")],
        [InlineKeyboardButton("Задание 4", callback_data="task_4"),
         InlineKeyboardButton("Задание 8", callback_data="task_8"),
         InlineKeyboardButton("Задание 9", callback_data="task_9")],
        [InlineKeyboardButton("Задание 17", callback_data="task_17"),
         InlineKeyboardButton("Задание 22", callback_data="task_22"),
         InlineKeyboardButton("Задание 27", callback_data="task_27")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text("Добро пожаловать! Выберите задание:", reply_markup=reply_markup)
    context.user_data['difficulty_message'] = message


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("🛠 Запускаем бота...")

    # Запускаем бота
    application.run_polling()

    logger.info("⚠ Завершение работы программы.")


if __name__ == "__main__":
    main()
