from time import sleep

import telebot
import datetime
import asyncio
#  import urllib.request  # request нужен для загрузки файлов от пользователя
import sqlite3
from multiprocessing import Process

con = sqlite3.connect("res/db/userdata.db")
cur = con.cursor()

# con.commit()


token = "6203295649:AAGtOD-fl1vXhUGqxIqcp5xbkFjQ35TyGi0"
bot = telebot.TeleBot(token)

HELP_TEXT = '''
Напиши /settime, а затем время по МСК без : . / и т.д. (например, 1700), чтобы выбрать время для напоминания вечером, когда ты будешь скидывать краткое описание своего дня и до 3х фотографий.
Получить свой архив воспоминаний можно командой /getmagazine
Написав /??? выбери время для получения с утра парочки анекдотов.

'''

example_magazine = {"userId1": [["day1text", "day1photo1", "day1photo2", "day1photo3"], ["day2text", "day2photo1", "day2photo2", "day2photo3"]], "userId2": ["messageId1", "messageId2"]}
"userId1:day1Text/day1photo1/day1Photo2*day2Text/day2photo1;userId2"


def check_time_to_send():
    time_list = [i[0] for i in sqlite3.connect("res/db/userdata.db").cursor().execute('SELECT time from time').fetchall()]
    while True:
        current_time = datetime.datetime.now().strftime('%H%M')
        if int(current_time) in time_list:
            curr_users = sqlite3.connect("res/db/userdata.db").cursor().execute(f'SELECT user from time WHERE time = "{current_time}"').fetchall()[0][0].split("/").pop(-1)
            for userid in curr_users:
                bot.send_message(userid, "Пора поделиться фотографиями за сегодня!")
        sleep(60)
        check_time_to_send()


# _______________________________________________________ВРЕМЯ__________________________________________________________
is_wait_time = False


def change_wait_time():
    global is_wait_time
    is_wait_time = False


def check_time(time, userid):
    if len(time) == 4 and time.isdigit():
        set_time(time, userid)
    else:
        bot.send_message(userid, "Время не было установлено. Напишите /settime снова и введите 4 цифры без других смволов.")


def set_time(time, userid):
    con = sqlite3.connect("res/db/userdata.db")
    cur = con.cursor()

    old_time = cur.execute(f'SELECT time FROM time WHERE user LIKE "%{userid}%"').fetchall()[0][0] if len(
        cur.execute(f'SELECT time FROM time WHERE user LIKE "%{userid}%"').fetchall()) != 0 else -1  # Прошлое время юзера, если новый юзер то -1
    users_in_new_time = cur.execute(f'SELECT user FROM time WHERE time = "{time}"').fetchall()[0][0] if len(
        cur.execute(f'SELECT user FROM time WHERE time = "{time}"').fetchall()) != 0 else ""  # Строка с пользователями для НОВОГО времени, если время ещё не исполь. то ""
    users_in_old_time = cur.execute(f'SELECT user FROM time WHERE time = "{old_time}"').fetchall()[0][0] if len(cur.execute(
            f'SELECT user FROM time WHERE time = "{old_time}"').fetchall()) != 0 else ""  # Строка с пользователями для СТАРОГО времени, если время ещё не исполь. то "" (такое возможно?)

    changeReq1 = f'UPDATE time SET time = "{time}", user = "{users_in_new_time + str(userid) + "/"}" WHERE time = "{time} time" AND user = "{users_in_new_time}";'  # Добавляем привязку к времени
    changeReq2 = f'UPDATE time SET time = "{old_time}", user = "{users_in_old_time.replace(str(userid) + "/", "")}" WHERE time = "{old_time}" AND user = "{users_in_old_time}";'  # Отвязываем юзера от прошлого времени
    print("!_!_!  ", changeReq2)
    createReq = f'INSERT INTO time (time, user) VALUES ("{time}", "{str(userid) + "/"}");'
    # deleteReq = f'UPDATE time SET time = "{old_time}", user = "{users_in_new_time + userid + "/"}" WHERE time = "{old_time} time" AND user = "{users_in_new_time}";'


    if old_time == -1:  # Если новый пользователь
        if len(users_in_new_time) == 0:  # Если время не существует
            cur.execute(createReq)  # добавляем время и юзера
        else:  # Новый пользователь, но время уже успользуется -> добавляем ко времени нового юзера
            cur.execute(changeReq1)  # добавляем юзера к времени
    else:  # Юзер уже превязан к времени. -> Удаляем привязку к старому и добавляем новую.
        cur.execute(changeReq2)
        if len(users_in_new_time) == 0:  # Если время не существует
            cur.execute(createReq)  # добавляем время и юзера
        else:  # Время уже успользуется -> добавляем ко времени юзера
            cur.execute(changeReq1)  # добавляем юзера к времени

    con.commit()
# ______________________________________________________________________________________________________________________


# _______________________________________________________КОМАНДЫ________________________________________________________

@bot.message_handler(commands=['start'])
def welcome_start(message):
    bot.send_message(message.chat.id, 'Привет, я могу составить архив твоих воспоминаний! Как мной пользоваться можно узнать, написав мне /help')


@bot.message_handler(commands=['help'])
def welcome_help(message):
    bot.send_message(message.chat.id, HELP_TEXT)


@bot.message_handler(commands=['settime'])
def welcome_help(message):
    global is_wait_time
    bot.send_message(message.chat.id, 'Введите время в которое вам будет удобно получать уведомление так "1720"'
                                      ' для получения в 17:20. Для отмены напишите -1 или отмена.')
    is_wait_time = True


@bot.message_handler(commands=['getmagazine'])
def welcome_help(message):
    bot.send_message(message.chat.id, '...')

# ______________________________________________________________________________________________________________________


# _______________________________________________________ОБРАБОТКА ТЕКСТА_______________________________________________
@bot.message_handler(content_types=["text"])
def text(message):
    if is_wait_time:  # ожидается установка времени
        check_time(message.text, message.from_user.id)
        change_wait_time()
    elif message.text == "id":
        bot.send_message(message.chat.id, "chat id is " + str(message.chat.id))
    elif message.text == "??":
        bot.send_message(message.from_user.id, "user id is " + str(message.from_user.id))


# @bot.message_handler(content_types=["text"])
# def text(message):
#     if message.text == 'photo':
#         file = open('photo.png', 'rb')
#         bot.send_photo(message.chat.id, file)
#
#
# @bot.message_handler(content_types=["text"])
# def text(message):
#     if message.text == 'document':
#         file = open('file.txt', 'rb')
#         bot.send_document(message.chat.id, file)

# ______________________________________________________________________________________________________________________


def run_bot():
    bot.polling()


if __name__ == "__main__":
    Process(target=run_bot).start()
    Process(target=check_time_to_send).start()



# con.close()
print()





# import telegram
# from telegram.ext import Updater, CommandHandler, MessageHandler, Application
# # ITEMS_FILE = "items.csv"
#
# token = "Token"
# bot = telegram.Bot
#
#
#
#
# async def start(update, context):
#     await update.message.reply_html (rf"Welcome to our clothing store bot.", )
#
#
# async def help(update, context):
#     await update.message.reply_html("Type /sell to view the available items for purchase.")
#
#
# # @bot.message_handler(content_types=['document'])
#
# # def handle_document(bot, update):
# #     file_id = update.message.document.file_id
# #     file = bot.get_file(file_id)
# #     file.download('путь/к/файлу')
#
# # def handle_docs_photo(message):
# #     try:
# #         chat_id = message.chat.id
# #         file_info = bot.get_file(message.document.file_id)
# #         downloaded_file = bot.download_file(file_info.file_path)
# #
# #         src = 'C:/Python/Project/tg_bot/files/received/' + message.document.file_name;
# #         with open(src, 'wb') as new_file:
# #             new_file.write(downloaded_file)
# #
# #         bot.reply_to(message, "Пожалуй, я сохраню это")
# #     except Exception as e:
# #         bot.reply_to(message, e)
# #
# # def upload_handler(update, user_data):
# #     # file_id = update.message.document.file_id
# #     # file_id = update.message.document.
# #     # file_id = update.
# #     # user_data['file_id'] = file_id
# #     update.message.reply_text('Файл успешно загружен.')
# #
# #
# # def download_handler(update, user_data):
# #     file_id = user_data.get('file_id')
# #     if file_id:
# #         # file = bot.get_file(file_id)
# #         file = telegram.Bot.get_file(file_id)
# #         file.download('путь/к/файлу')
# #         update.message.reply_text('Файл успешно сохранен.')
# #     else:
# #         update.message.reply_text('Файл не найден. Отправьте файл в чат и введите команду /upload.')
# #
#
#
#
#
# # def sell(bot, update):
# #     items = pd.read_csv(ITEMS_FILE)
# #     item_index = random.randint(0, len(items) - 1)
# #     bot.send_photo(chat_id=update.message.chat_id, photo=items.iloc[item_index]['Image'])
# #     bot.send_message(chat_id=update.message.chat_id, text=items.iloc[item_index]['Description'])
#
#
# # def inline_sell(bot, update):
# #     query = update.inline_query.query
# #     if not query:
# #         return
# #     items = pd.read_csv(ITEMS_FILE)
# #     results = []
# #     for index, row in items.iterrows():
# #         if query.lower() in row['Name'].lower():
# #             results.append(
# #                 telegram.InlineQueryResultPhoto(
# #                     id=index,
# #                     photo_url=row['Image'],
# #                     thumb_url=row['Image'],
# #                     caption=row['Description']
# #                 )
# #             )
# #     bot.answer_inline_query(update.inline_query.id, results)
#
#
#
#
# def main():
#     # updater = Updater(token='6203295649:AAGtOD-fl1vXhUGqxIqcp5xbkFjQ35TyGi0')
#     application = Application.builder().token("6203295649:AAGtOD-fl1vXhUGqxIqcp5xbkFjQ35TyGi0").build()
#
#     # dp = updater.dispatcher
#     application.add_handler(CommandHandler('start', start))
#     application.add_handler(CommandHandler('help', help))
#
#
#     # application.add_handler(CommandHandler('upload', upload_handler))
#     # application.add_handler(CommandHandler('down', download_handler))
#
#     # application.add_handler(MessageHandler(content_types=['document']))
#     application.run_polling()
#     # dp.add_handler(CommandHandler('sell', sell))
#     # dp.add_handler(telegram.InlineQueryHandler(inline_sell))
#     # updater.start_polling()
#     # updater.idle()
#
# # @bot.message_handler(content_types=['document'])
#
#
# if __name__ == '__main__':
#     main()
