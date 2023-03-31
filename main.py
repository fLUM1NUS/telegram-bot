import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Application

bot = telegram.Bot


async def start(update, context):
    await update.message.reply_html(
        rf"Welcome to our clothing store bot.",
    )


async def help(update, context):
    await update.message.reply_html("Type /sell to view the available items for purchase.")


def main():

    application = Application.builder().token("6203295649:AAGtOD-fl1vXhUGqxIqcp5xbkFjQ35TyGi0").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))

    application.run_polling()


if __name__ == '__main__':
    main()
