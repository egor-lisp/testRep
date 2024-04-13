from telebot import TeleBot

BOT_TOKEN = '5637295535:AAEJCZnlZFXZSUA8BKqzHWYxTPzXThaLa84'  # Токен бота
USER_IDS = [948118653]  # Айди пользователей куда отправлять

bot = TeleBot(token=BOT_TOKEN)


def send_alerts(text):
    for user_id in USER_IDS:
        if len(text) > 4096:
            for x in range(0, len(text), 4096):
                bot.send_message(user_id, text[x:x + 4096], parse_mode='markdown')
        else:
            bot.send_message(user_id, text, parse_mode='markdown')


def send_file(text, filename):
    file = open(filename, 'rb')
    for user_id in USER_IDS:
        bot.send_document(chat_id=user_id, document=file, caption=text)
    file.close()
