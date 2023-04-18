import telebot
import datetime
#  import urllib.request  # request нужен для загрузки файлов от пользователя
import sqlite3
import openai
from time import sleep
from multiprocessing import Process

# from PIL import Image

import cv2
import numpy as np
import random
import rpack
from fractions import Fraction
from math import prod
import colorgram
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


# ______________________________________________________________________________________________________________________

def get_gominant_color(images):
    dominant_colors = []
    for image in images:
        colors = colorgram.extract(image, 10)

        rgb_colors = []
        for color in colors:
            r = color.rgb.r
            g = color.rgb.g
            b = color.rgb.b
            rgb_colors.append((r, g, b))

        dominant_color = max(set(rgb_colors), key=rgb_colors.count)
        dominant_colors.append(dominant_color)

    returned = []
    for i in range(3):
        cur_color = 0
        for j in range(len(images)):
            cur_color += dominant_colors[j][i]
        returned.append(cur_color // len(images))
    return returned



def resize_guide(image_size, unit_shape, target_ratio):
    aspect_ratio = Fraction(*image_size).limit_denominator()
    horizontal = aspect_ratio.numerator
    vertical = aspect_ratio.denominator
    target_area = prod(unit_shape) * target_ratio
    unit_length = (target_area / (horizontal * vertical)) ** .5
    return int(horizontal * unit_length), int(vertical * unit_length)


def make_border(image, value, border=16):
    return cv2.copyMakeBorder(
        image,
        top=border,
        bottom=border,
        left=border,
        right=border,
        borderType=cv2.BORDER_CONSTANT,
        value=value
    )


def rotate_image(image, angle, dominant_color):
    h, w = image.shape[:2]
    cX, cY = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    return cv2.warpAffine(image, M, (nW, nH), borderMode=cv2.BORDER_CONSTANT, borderValue=dominant_color)  # -!-!-!-!-


def make_collage(image_files, output_file,
                 exponent=0.8, border=16, max_degree=15, unit_shape=(1280, 720),
                 resize_images=True, image_border=False, rotate_images=True, limit_shape=True):
    images = [cv2.imread(name) for name in image_files]
    dominant_color = get_gominant_color(image_files)
    size_hint = [exponent ** i for i in range(len(images))]

    if resize_images:
        resized_images = []
        for image, hint in zip(images, size_hint):
            height, width = image.shape[:2]
            guide = resize_guide((width, height), unit_shape, hint)
            resized = cv2.resize(image, guide, interpolation=cv2.INTER_AREA)
            if image_border:
                resized = make_border(resized, (255, 255, 255), border)
            resized_images.append(resized)
        images = resized_images
    else:
        sorted_images = []
        for image in sorted(images, key=lambda x: -prod(x.shape[:2])):
            if image_border:
                image = make_border(image, (255, 255, 255), border)
            sorted_images.append(image)
        images = sorted_images

    sizes = []
    processed_images = []
    for image in images:
        if rotate_images:
            image = rotate_image(image, random.randrange(-max_degree, max_degree + 1), dominant_color)
        processed = make_border(image, dominant_color, border)  # -!-!-!-!-
        processed_images.append(processed)
        height, width = processed.shape[:2]
        sizes.append((width, height))

    if limit_shape:
        max_side = int((sum([w * h for w, h in sizes]) * 2) ** .5)
        packed = rpack.pack(sizes, max_width=max_side, max_height=max_side)
    else:
        packed = rpack.pack(sizes)

    shapes = [(x, y, w, h) for (x, y), (w, h) in zip(packed, sizes)]
    rightmost = sorted(shapes, key=lambda x: -x[0] - x[2])[0]
    bound_width = rightmost[0] + rightmost[2]
    downmost = sorted(shapes, key=lambda x: -x[1] - x[3])[0]
    bound_height = downmost[1] + downmost[3]

    collage = np.full([bound_height, bound_width, 3], dominant_color, dtype=np.uint8)  # -!-!-!-!-

    for image, (x, y, w, h) in zip(processed_images, shapes):
        collage[y:y + h, x:x + w] = image

    collage = cv2.GaussianBlur(collage, (3, 3), cv2.BORDER_DEFAULT)
    cv2.imwrite(output_file, collage)

# ______________________________________________________________________________________________________________________

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
is_wait_count = False


def get_day_text(userid, day_text):
    global is_wait_day_text, is_wait_count
    is_wait_day_text = False
    is_wait_count = True
    bot.send_message(userid, "Сколько фото сегоднешнего дня вы пришлёте?")
    wait_count(userid, day_text)

    # bot.send_message(userid, day_text)


def wait_count(userid, day_text):
    pass



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
    elif is_wait_count:
        get_photos(message.from_user.id)
    elif is_wait_day_text:
        day_text = message.text
        get_day_text(message.from_user.id, day_text)
    elif message.text == "id":
        bot.send_message(message.chat.id, "chat id is " + str(message.chat.id))
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



def start_timer_us():
    sleep(5)
    check_time_to_send_add()
    print("Timer usual started")


def start_timer_morn():
    sleep(5)
    check_time_to_send_morn()
    print("Timer morn started")


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
