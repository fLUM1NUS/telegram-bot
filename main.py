import telebot
from telebot import apihelper  # Нужно для работы Proxy
import urllib.request  # request нужен для загрузки файлов от пользователя

token = "6203295649:AAGtOD-fl1vXhUGqxIqcp5xbkFjQ35TyGi0"
bot = telebot.TeleBot(token)

HELP_TEXT = '''
tg bot
бот на каждый день в установленное пользователем время бот пишет доброе утро и отправляет погоду на сегодня и 2 анекдота и какие сегодня праздники
вечером бот в установленное время бот предлагает отправить пользователю 3 фотографии дня что бы сохранить их
по желанию бот формирует журнал воспоминаний
'''

example_magazine = {"userId1": [["day1text", "day1photo1", "day1photo2", "day1photo3"], ["day2text", "day2photo1", "day2photo2", "day2photo3"]], "userId2": ["messageId1", "messageId2"]}
"userId1:day1Text/day1photo1/day1Photo2*day2Text/day2photo1;userId2"

@bot.message_handler(content_types=["text"])
def text(message):
    if message.text == 'hello':
        bot.send_message(message.chat.id, 'И тебе hello')


@bot.message_handler(content_types=["text"])
def text(message):
    if message.text == 'photo':
        file = open('photo.png', 'rb')
        bot.send_photo(message.chat.id, file)


@bot.message_handler(content_types=["text"])
def text(message):
    if message.text == 'document':
        file = open('file.txt', 'rb')
        bot.send_document(message.chat.id, file)



@bot.message_handler(commands=['start'])
def welcome_start(message):
    bot.send_message(message.chat.id, 'Привет, я готов к работе. Информацию можно получить, написав мне /help')


@bot.message_handler(commands=['help'])
def welcome_help(message):
    bot.send_message(message.chat.id, HELP_TEXT)


@bot.message_handler(commands=['settime'])
def welcome_help(message):
    bot.send_message(message.chat.id, '...')


@bot.message_handler(commands=['getmagazine'])
def welcome_help(message):
    bot.send_message(message.chat.id, '...')


bot.polling()




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
#     await update.message.reply_html(
#         rf"Welcome to our clothing store bot.",
#     )
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
