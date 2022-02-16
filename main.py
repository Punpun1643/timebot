from telegram.ext import (Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext)
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from datasource import DataSource


import os
import threading
import time
import datetime

TOKEN = os.getenv('TOKEN')
ADD_REMINDER_TEXT = 'Add a reminder ⏰'
INTERVAL = 30
ENTER_MESSAGE, ENTER_TIME = range(2)
dataSource = DataSource(os.environ.get("DATABASE_URL"))


def start_handler(update, context):
    update.message.reply_text("Hello, creator!", reply_markup=add_reminder_button())


def add_reminder_button():
    keyboard = [[KeyboardButton(ADD_REMINDER_TEXT)]]
    return ReplyKeyboardMarkup(keyboard)


def add_reminder_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Please enter message of the reminder: ")
    return ENTER_MESSAGE


def enter_message_handler(update: Update, context: CallbackContext):
    # save user message
    context.user_data['message_text'] = update.message.text
    update.message.reply_text("Please enter a time when bot should remind (DD/MM/YYYY HH:MM): ")
    return ENTER_TIME


def enter_time_handler(update: Update, context: CallbackContext):
    message_text = context.user_data['message_text']
    time = datetime.datetime.strptime(update.message.text, "%d/%m/%Y %H:%M")
    message_data = dataSource.create_reminder(update.message.chat_id, message_text, time)
    update.message.reply_text("Your reminder ⭐️" + "\n" + message_data.__repr__())
    return ConversationHandler.END


def start_check_reminders_task():
    thread = threading.Thread(target=check_reminders, args=())
    thread.daemon = True
    thread.start()


def check_reminders():
    while True:
        for reminder_data in dataSource.get_all_reminders():
            if reminder_data.should_be_fired():
                dataSource.fire_reminder(reminder_data.reminder_id)
                updater.bot.send_message(reminder_data.reminder_id, reminder_data.message)
        time.sleep(INTERVAL)


if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(ADD_REMINDER_TEXT), add_reminder_handler)],
        states={
            ENTER_MESSAGE: [MessageHandler(Filters.all, enter_message_handler)],
            ENTER_TIME: [MessageHandler(Filters.all, enter_time_handler)]
        },
        fallbacks=[]
    )
    updater.dispatcher.add_handler(conv_handler)
    dataSource.create_tables()
    updater.start_polling()
    start_check_reminders_task()
