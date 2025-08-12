import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = '8491036994:AAEsFy6M0uzsua3XFPsOt_g7rNd4zq7CbTk'
ADMIN_IDS = [5048547918]

reply_map = {}
last_user_messages = {}
user_warnings = {}
banned_users = {}
MAX_WARNINGS = 3
BLOCK_TIME = 60

# Чёрный список слов и фраз
banned_words = [
    "мат", "оскорбление", "порно", "sex", "сука", "блядь",
    "идиот", "лох", "тварь", ".exe", ".bat", ".zip", ".rar"
    "спам",
    "без вложений", "рассылка", "раздача", "заработок", "crypto",
    "заработай легко", "быстрый заработок", "пассивный доход", "вложи один раз",
    "переходи по ссылке", "перейди по ссылке", "жми сюда", "жми на ссылку",
    "скачай файл", "пройди регистрацию", "получи доступ", "зарабатывай на дому",
    "инвестируй", "быстрые деньги", "торговый бот", "казино",
    "ставки", "пари", "беттинг", "только сегодня", "акция действует", "дешевле не будет"
    "гандон", "котакбас", "мал", "шешен", "шшн",  "ска", "пидр", "секс", "казик", "гей",  "уебок", "телка", "шлюха", "мамка", "ебал", "транс", "сучка", "ебут", "сукин", "пизда",   "ебаный", "ебаная",  "выебу",  "нахуй", "мразь",  "ебливая",  "хуйни",  "ебаной", "ебливая",  "суука", "негр", "проститутка"                    
]

# Чёрный список доменов
blacklisted_domains = [
    "pornhub.com", "xvideos.com", "xnxx.com", 
    "ok.ru", "onlyfans.com"
    "bit.ly", "goo.gl",
    "anonfiles.com", "disk.yandex", "dropbox.com"

]

# Чёрный список расширений файлов
blacklisted_file_ext = [
    ".exe", ".bat", ".cmd", ".scr", ".pif", ".jar", ".vbs",
    ".msi", ".apk", ".zip", ".rar", ".7z"
]


# === Команда /rules ===
async def handle_rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = (
        "📜 *Правила использования бота:*\n\n"
        "1. 🚫 Запрещено использовать нецензурную лексику\n"
        "2. 🚫 Запрещена реклама и спам\n"
        "3. 🚫 Оскорбления и провокации недопустимы\n"
        "4. 🔁 Повтор одинаковых сообщений запрещён\n"
        "5. ⏱ За 3 нарушения — временная блокировка\n\n"
        "✅ Соблюдайте правила, чтобы общение было комфортным."
    )
    await update.message.reply_text(rules_text, parse_mode="Markdown")


# === Команда /start ===
async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎓 Добро пожаловать!\n"
        "Вы на связи с менеджером канала «История Казахстана | ЕНТ 2026» 🇰🇿\n"
        "Меня зовут Ерлан — рад вас приветствовать.\n"
        "                                          \n"
        "Чем могу быть полезен❓\n"
        "📜 Также ознакомьтесь с правилами ниже:"
    )
    await update.message.reply_text(welcome_text)
    await handle_rules_command(update, context)


# === Пользователь пишет ===
async def handle_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "Без username"
    now = time.time()

    if user_id in banned_users:
        if now < banned_users[user_id]:
            return
        else:
            del banned_users[user_id]
            user_warnings[user_id] = 0

    text = update.message.text.strip().lower() if update.message.text else ""

    # Антиспам
    if last_user_messages.get(user_id) == text:
        await update.message.reply_text("🚫 Не повторяй одно и то же сообщение.")
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        return
    last_user_messages[user_id] = text

    # Фильтр запрещённых слов
    for word in banned_words:
        if word in text:
            await update.message.reply_text("🚫 Сообщение содержит запрещённые слова или ссылки.")
            user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
            return

    # Фильтр доменов
    for domain in blacklisted_domains:
        if domain in text:
            await update.message.reply_text("🚫 Сообщение содержит запрещённый домен.")
            user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
            return

    # Фильтр документов
    if update.message.document:
        filename = update.message.document.file_name.lower()
        for ext in blacklisted_file_ext:
            if filename.endswith(ext):
                await update.message.reply_text("🚫 Запрещённый тип файла.")
                return

    # Блокировка за нарушения
    if user_warnings.get(user_id, 0) >= MAX_WARNINGS:
        banned_users[user_id] = now + BLOCK_TIME
        await update.message.reply_text("🔒 Вы временно заблокированы за нарушение правил.")
        return

    # Пересылка админу
    sent = None
    if update.message.text:
        sent = await context.bot.send_message(
            chat_id=ADMIN_IDS[0],
            text=f"📨 От @{username} (ID: {user_id}):\n\n{update.message.text}"
        )
    elif update.message.photo:
        sent = await context.bot.send_photo(
            chat_id=ADMIN_IDS[0],
            photo=update.message.photo[-1].file_id,
            caption=f"📸 Фото от @{username} (ID: {user_id})"
        )
    elif update.message.document:
        sent = await context.bot.send_document(
            chat_id=ADMIN_IDS[0],
            document=update.message.document.file_id,
            caption=f"📄 Документ от @{username} (ID: {user_id})"
        )
    elif update.message.video:
        sent = await context.bot.send_video(
            chat_id=ADMIN_IDS[0],
            video=update.message.video.file_id,
            caption=f"📹 Видео от @{username} (ID: {user_id})"
        )

    if sent:
        reply_map[sent.message_id] = user_id


# === Админ отвечает на сообщение ===
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    reply = update.message.reply_to_message
    if not reply:
        return

    original_msg_id = reply.message_id
    if original_msg_id not in reply_map:
        await update.message.reply_text("❌ Не удалось определить получателя.")
        return

    user_id = reply_map[original_msg_id]

    try:
        if update.message.text:
            await context.bot.send_message(chat_id=user_id, text=update.message.text)
        elif update.message.photo:
            await context.bot.send_photo(chat_id=user_id, photo=update.message.photo[-1].file_id)
        elif update.message.document:
            await context.bot.send_document(chat_id=user_id, document=update.message.document.file_id)
        elif update.message.video:
            await context.bot.send_video(chat_id=user_id, video=update.message.video.file_id)
        await update.message.reply_text("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке: {e}")


# === Команды админа /ban, /unban, /stats ===
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❗ Формат: /ban <user_id> <время_в_минутах>")
        return

    try:
        user_id = int(args[0])
        minutes = int(args[1])
        banned_users[user_id] = time.time() + minutes * 60
        await update.message.reply_text(f"✅ Пользователь {user_id} заблокирован на {minutes} мин.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    try:
        user_id = int(context.args[0])
        if user_id in banned_users:
            del banned_users[user_id]
            await update.message.reply_text(f"✅ Пользователь {user_id} разблокирован.")
        else:
            await update.message.reply_text("ℹ️ Этот пользователь не заблокирован.")
    except:
        await update.message.reply_text("❌ Используй: /unban <user_id>")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    total_users = len(last_user_messages)
    total_banned = len(banned_users)
    total_warnings = sum(user_warnings.values())

    await update.message.reply_text(
        f"📊 Статистика:\n"
        f"👤 Пользователей: {total_users}\n"
        f"🔒 Заблокировано: {total_banned}\n"
        f"⚠️ Нарушений: {total_warnings}"
    )

# === Команда /warnings ===
async def warnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❗ Используй: /warnings <user_id>")
        return
    try:
        user_id = int(context.args[0])
        warns = user_warnings.get(user_id, 0)
        await update.message.reply_text(f"⚠️ У пользователя {user_id} {warns} предупреждений.")
    except:
        await update.message.reply_text("❌ Неверный формат команды.")

# === Команда /clearwarns ===
async def clearwarns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) != 2:
        await update.message.reply_text("❗ Используй: /clearwarns <user_id> <кол-во>")
        return
    try:
        user_id = int(context.args[0])
        count = int(context.args[1])
        current = user_warnings.get(user_id, 0)
        user_warnings[user_id] = max(0, current - count)
        await update.message.reply_text(f"✅ У пользователя {user_id} теперь {user_warnings[user_id]} предупреждений.")
    except:
        await update.message.reply_text("❌ Ошибка при выполнении команды.")

# === Команда /warn ===
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❗ Используй: /warn <user_id> <причина>")
        return
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:])
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        await update.message.reply_text(f"⚠️ Пользователю {user_id} выдано предупреждение. Причина: {reason}")
        if user_warnings[user_id] >= MAX_WARNINGS:
            banned_users[user_id] = time.time() + BLOCK_TIME
            await update.message.reply_text(f"🔒 Пользователь {user_id} заблокирован за превышение лимита предупреждений.")
    except:
        await update.message.reply_text("❌ Ошибка при выполнении команды.")


# === Запуск ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Пользователи
user_filter = ~filters.User(user_id=ADMIN_IDS)
app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & user_filter, handle_user))

# Ответы админа на сообщения
admin_reply_filter = filters.User(user_id=ADMIN_IDS) & filters.REPLY & ~filters.COMMAND
app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.VIDEO) & admin_reply_filter, handle_admin_reply))

# Команды
app.add_handler(CommandHandler("start", handle_start_command))
app.add_handler(CommandHandler("rules", handle_rules_command))
app.add_handler(CommandHandler("ban", ban_command))
app.add_handler(CommandHandler("unban", unban_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CommandHandler("warnings", warnings_command))
app.add_handler(CommandHandler("clearwarns", clearwarns_command))
app.add_handler(CommandHandler("warn", warn_command))


print("🤖 Бот запущен")
app.run_polling()
