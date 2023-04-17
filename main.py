import telebot
import datetime
#  import urllib.request  # request нужен для загрузки файлов от пользователя
import sqlite3
import openai
from time import sleep
from multiprocessing import Process
import logging


tg_token = "6203295649:AAGtOD-fl1vXhUGqxIqcp5xbkFjQ35TyGi0"
bot = telebot.TeleBot(tg_token)

openai.api_key = "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"

ARCHIVE_BOT_ID = "6286742171"
HELP_TEXT = '''
Напиши /settime, а затем время по МСК + 6 часов без : . / и т.д. (например, 1700), чтобы выбрать время для \
напоминания вечером, когда ты будешь скидывать краткое описание своего дня и до 3х фотографий.
Написав /setmorningtime выбери время для получения с утра парочки анекдотов.
Получить свой архив воспоминаний можно командой /getmagazine
'''

example_magazine = {"userId1": [["day1text", "day1photo1", "day1photo2", "day1photo3"], ["day2text", "day2photo1", "day2photo2", "day2photo3"]]}  # , "userId2": ["messageId1", "messageId2"]}
"userId1:day1Text/day1photo1/day1Photo2*day2Text/day2photo1;userId2"


def get_chatgpt_joke():
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Ты должен рассказывать анекдоты, если не знаешь, "
                                                "то придумай. Не говори мне о том что не можешь."},
                  {"role": "user", "content": "Расскажи анекдот. Пиши только само содержание анекдота без своих слов."}
                  ])["choices"][0]["message"]["content"]



def check_time_to_send_add():
    time_list = [i[0] for i in sqlite3.connect("res/db/userdata.db").cursor().execute('SELECT time from time').fetchall()]
    current_time = datetime.datetime.now().strftime('%H%M')
    if int(current_time) in time_list:
        try:
            curr_users = [sqlite3.connect("res/db/userdata.db").cursor().execute(f'SELECT user from time WHERE time = "{current_time}"').fetchall()[0][0].split("/").pop(0)]
            for userid in curr_users:
                bot.send_message(userid, "Пора поделиться фотографиями за сегодня!")
        except BaseException:
            pass
    sleep(60)
    check_time_to_send_add()


def check_time_to_send_morn():
    time_list = [i[0] for i in sqlite3.connect("res/db/userdata.db").cursor().execute('SELECT time from time_morn').fetchall()]
    joke = get_chatgpt_joke()
    current_time = datetime.datetime.now().strftime('%H%M')
    if int(current_time) in time_list:
        try:
            curr_users = [sqlite3.connect("res/db/userdata.db").cursor().execute(f'SELECT user from time_morn WHERE time = "{current_time}"').fetchall()[0][0].split("/").pop(0)]
            for userid in curr_users:
                bot.send_message(userid, ("Доброе утро!\n\nАнекдот дня:\n" + joke))
        except BaseException:
            pass
    sleep(60)
    check_time_to_send_morn()


def start_timer_us():
    sleep(5)
    check_time_to_send_add()
    print("Timer usual started")


def start_timer_morn():
    sleep(5)
    check_time_to_send_morn()
    print("Timer morn started")


# __________________________________________ВРЕМЯ УВЕДОМЛЕНИЯ ВЕЧЕРОМ___________________________________________________
is_wait_time_add = False


def change_wait_time_add():
    global is_wait_time_add
    is_wait_time_add = False


def check_time_add(time, userid):
    if ((len(time) == 4) and (time.isdigit()) and (0 < int(time[:2]) < 24) and (0 < int(time[2:]) < 60)) or (time == "-1"):
        set_time_add(time, userid)
    else:
        bot.send_message(userid, "Время не было установлено. Напишите /settime снова и введите 4 цифры без других смволов.")


def set_time_add(time, userid):
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
    createReq = f'INSERT INTO time (time, user) VALUES ("{time}", "{str(userid) + "/"}");'


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
    con.close()
    if time == "-1":
        bot.send_message(userid, "Уедомления отключены")
    else:
        bot.send_message(userid, f"Время вечернего уведомления установленно на {time[:2] + ':' +time[2:]}")
# ______________________________________________________________________________________________________________________


# __________________________________________ВРЕМЯ УВЕДОМЛЕНИЯ УТРОМ_____________________________________________________
is_wait_time_morn = False


def change_wait_time_morn():
    global is_wait_time_morn
    is_wait_time_morn = False


def check_time_add_morn(time, userid):
    if ((len(time) == 4) and (time.isdigit()) and (0 < int(time[:2]) < 24) and (0 < int(time[2:]) < 60)) or (time == "-1"):
        set_time_add_morn(time, userid)
    else:
        bot.send_message(userid, "Время не было установлено. Напишите /settimemorn снова и введите 4 цифры без других смволов.")


def set_time_add_morn(time, userid):
    con2 = sqlite3.connect("res/db/userdata.db")
    cur2 = con2.cursor()

    old_time = cur2.execute(f'SELECT time FROM time_morn WHERE user LIKE "%{userid}%"').fetchall()[0][0] if len(
        cur2.execute(f'SELECT time FROM time_morn WHERE user LIKE "%{userid}%"').fetchall()) != 0 else -1  # Прошлое время юзера, если новый юзер то -1
    users_in_new_time = cur2.execute(f'SELECT user FROM time_morn WHERE time = "{time}"').fetchall()[0][0] if len(
        cur2.execute(f'SELECT user FROM time_morn WHERE time = "{time}"').fetchall()) != 0 else ""  # Строка с пользователями для НОВОГО времени, если время ещё не исполь. то ""
    users_in_old_time = cur2.execute(f'SELECT user FROM time_morn WHERE time = "{old_time}"').fetchall()[0][0] if len(cur2.execute(
            f'SELECT user FROM time_morn WHERE time = "{old_time}"').fetchall()) != 0 else ""  # Строка с пользователями для СТАРОГО времени, если время ещё не исполь. то "" (такое возможно?)

    changeReq1 = f'UPDATE time_morn SET time = "{time}", user = "{users_in_new_time + str(userid) + "/"}" WHERE time = "{time} time" AND user = "{users_in_new_time}";'  # Добавляем привязку к времени
    changeReq2 = f'UPDATE time_morn SET time = "{old_time}", user = "{users_in_old_time.replace(str(userid) + "/", "")}" WHERE time = "{old_time}" AND user = "{users_in_old_time}";'  # Отвязываем юзера от прошлого времени
    createReq = f'INSERT INTO time_morn (time, user) VALUES ("{time}", "{str(userid) + "/"}");'


    if old_time == -1:  # Если новый пользователь
        if len(users_in_new_time) == 0:  # Если время не существует
            cur2.execute(createReq)  # добавляем время и юзера
        else:  # Новый пользователь, но время уже успользуется -> добавляем ко времени нового юзера
            cur2.execute(changeReq1)  # добавляем юзера к времени
    else:  # Юзер уже превязан к времени. -> Удаляем привязку к старому и добавляем новую.
        cur2.execute(changeReq2)
        if len(users_in_new_time) == 0:  # Если время не существует
            cur2.execute(createReq)  # добавляем время и юзера
        else:  # Время уже успользуется -> добавляем ко времени юзера
            cur2.execute(changeReq1)  # добавляем юзера к времени

    con2.commit()
    con2.close()
    if time == "-1":
        bot.send_message(userid, "Утренние уведомления отключены")
    else:
        bot.send_message(userid, f"Время утреннего уведомления установленно на {time[0:2] + ':' +time[2:]}")
# ______________________________________________________________________________________________________________________

# __________________________________________ЗАГРУЗКА ДНЯ________________________________________________________________  # ----------------------------------------------------------------


is_wait_day_text = False
is_wait_day_photos = False


def get_day_text(userid, day_text):
    global is_wait_day_text, is_wait_day_photos
    is_wait_day_text = False
    is_wait_day_photos = True

    bot.send_message(userid, day_text)


def get_photos(userid):  # , day_text):
    global is_wait_day_photos
    is_wait_day_photos = False

# ______________________________________________________________________________________________________________________


# __________________________________________КОМАНДЫ_____________________________________________________________________
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет, я могу составить архив твоих воспоминаний! Как мной пользоваться можно '
                                      'узнать, написав мне /help')


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, HELP_TEXT)


@bot.message_handler(commands=['settime'])
def settime(message):
    global is_wait_time_add
    bot.send_message(message.chat.id, 'Введите время в которое вам будет удобно получать напоминание о пополнение '
                                      'архива так: "1720" для получения в 17:20. Для отмены напишите -1 или отмена.')
    is_wait_time_add = True


@bot.message_handler(commands=['settimemorn'])
def settimemorn(message):
    global is_wait_time_morn
    bot.send_message(message.chat.id, 'Введите время в которое вам будет удобно получать утренний анекдот '
                                      'так: "1720" для получения в 17:20. Для отмены напишите -1 или отмена.')
    is_wait_time_morn = True


@bot.message_handler(commands=['getmagazine'])
def getmagazine(message):
    global is_wait_day_text
    bot.send_message(message.chat.id, '...')
    is_wait_day_text = True


@bot.message_handler(commands=['upload'])
def upload(message):
    global is_wait_day_text
    bot.send_message(message.chat.id, "Опишите свой день в пару слов")
    is_wait_day_text = True


# ______________________________________________________________________________________________________________________

# __________________________________________ОБРАБОТКА ТЕКСТА____________________________________________________________

@bot.message_handler(content_types=["text"])
def text(message):
    if is_wait_time_add:  # ожидается установка времени
        check_time_add(message.text, message.from_user.id)
        change_wait_time_add()
    elif is_wait_time_morn:
        check_time_add_morn(message.text, message.from_user.id)
        change_wait_time_morn()
    elif is_wait_day_text:
        day_text = message.text
        get_day_text(message.from_user.id, day_text)
    elif message.text == "id":
        bot.send_message(message.chat.id, "chat id is " + str(message.chat.id))
    elif message.text == "??":
        bot.send_message(message.from_user.id, "user id is " + str(message.from_user.id))
    elif message.text == "test1":
        bot.send_message(message.chat.id, message.id)


# @bot.message_handler(content_types=['photo'])
# def handle_photos(message):
#     global is_wait_day_photos
#     if is_wait_day_photos:
#         chat_id = message.chat.id
#         photos = message.photo
#         print(photos, "\n", "class:", "\n", type(photos), photos[0], "\n", "len:", len(photos))
#         num_photos = len(photos)
#         print(f"Received {num_photos} photo(s) from user {chat_id}")
#         # for i in range(num_photos):
#         #     bot.send_photo(chat_id, photos[i].file_id)
#         bot.reply_to(message, f"Received {num_photos} photo(s)")
#         get_photos(message.from_user.id)
#
#         # for photo in message.photo:
#         #     file_id = photo.file_id
#         #     bot.send_photo(message.chat.id, file_id)

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    photos = message.photo


    last_photo = photos[-1]  # получаем последнюю фотографию из списка
    file_id = last_photo.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    bot.send_photo(message.chat.id, downloaded_file)
    with open(("photos/" + str(message.chat.id) + datetime.date.today().strftime("-%d-%m-%y-") + datetime.datetime.now().strftime('%f') + ".jpg"), mode="wb+") as f:
        f.write(downloaded_file)





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
    sleep(1)
    print("!")
    bot.polling()


if __name__ == "__main__":
    Process(name="bot", target=run_bot).start()
    Process(name="timer us", target=start_timer_us).start()
    Process(name="timer morn", target=start_timer_morn).start()
    bot.send_message("901913162", "!!!")
    print("Process started")


print()
