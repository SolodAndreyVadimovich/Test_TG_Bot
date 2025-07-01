import telebot
from telebot import types
import sqlite3
import logging
from datetime import datetime

# === CONFIG ===
TOKEN = '8167073780:AAHxfJn7cQP_qlIigZOLQqstv8VCnVYwJ-w'  # вставь сюда свой токен от BotFather
bot = telebot.TeleBot(TOKEN)

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === DATABASE ===
conn = sqlite3.connect('notes.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        timestamp TEXT
    )
''')
conn.commit()


# === COMMAND HANDLERS ===
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Добавить заметку"),
               types.KeyboardButton("📋 Мои заметки"),
               types.KeyboardButton("❌ Удалить заметку"))
    bot.send_message(message.chat.id, "Привет! Я бот-записная книжка. Выбери действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "📝 Добавить заметку")
def add_note(message):
    bot.send_message(message.chat.id, "Отправь мне текст заметки:")
    bot.register_next_step_handler(message, save_note)


def save_note(message):
    user_id = message.from_user.id
    text = message.text.strip()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO notes (user_id, text, timestamp) VALUES (?, ?, ?)', (user_id, text, timestamp))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Заметка сохранена!")


@bot.message_handler(func=lambda message: message.text == "📋 Мои заметки")
def list_notes(message):
    user_id = message.from_user.id
    cursor.execute('SELECT id, text FROM notes WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "У тебя пока нет заметок.")
    else:
        response = "🗒 Твои заметки:\n"
        for idx, row in enumerate(rows, start=1):
            response += f"{idx}. {row[1]}\n"
        bot.send_message(message.chat.id, response)


@bot.message_handler(func=lambda message: message.text == "❌ Удалить заметку")
def delete_note_prompt(message):
    user_id = message.from_user.id
    cursor.execute('SELECT id, text FROM notes WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "У тебя пока нет заметок для удаления.")
        return

    markup = types.InlineKeyboardMarkup()
    for idx, row in enumerate(rows, start=1):
        markup.add(types.InlineKeyboardButton(f"Удалить: {idx}. {row[1][:30]}", callback_data=f"del_{row[0]}"))
    bot.send_message(message.chat.id, "Выбери заметку для удаления:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def callback_delete(call):
    note_id = int(call.data.split("_")[1])
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "Заметка удалена")
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="✅ Заметка удалена.")


# === START BOT ===
bot.polling(none_stop=True)
