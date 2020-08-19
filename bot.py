#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import auto_ru_parcer
import stats
import pickle
import schedule1
import time
from transliterate import translit
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from personal import TOKEN
MODEL = range(1)
MARK_NEW, MODEL_NEW, PRICES_NEW = range(3)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Приветствую тебя, любитель крутыш тачил!')


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Я ни фига не умею, а-ха-ха')


def echo(update, context):
    """Echo the user message."""
    # update.message.reply_text(update.message.text)


def list_marks(update, context):
    update.message.reply_text('Ищу доступные марки на авто.ру')
    try:
        with open("marks.txt", "rb") as fp:   # Unpickling
            marks = pickle.load(fp)
    except Exception:
        marks = sorted(auto_ru_parcer.list_marks())
        with open("marks.txt", "wb") as fp:   #Pickling
            pickle.dump(marks, fp)
    update.message.reply_text('\n'.join(marks))


def list_models(update, context):
    update.message.reply_text('Введите название интересующей марки\nДля подсказки введите /marks')
    return MODEL



def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Ну и катайся на метро',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def get_models(update, context):
    mark = update.message.text
    with open("marks.txt", "rb") as fp:   # Unpickling
            marks = pickle.load(fp)
    update.message.reply_text('ищу ' + mark)
    mark = find_correct(mark, marks)
    logger.info("Models of %s", update.message.text)
    if mark in marks:
        try:
            with open("models/{}.txt".format(mark), "rb") as fp:   # Unpickling
                models = pickle.load(fp)
        except Exception:
            mark, models = auto_ru_parcer.list_models(mark)
            models = sorted(models)
            with open("models/{}.txt".format(mark), "wb") as fp:   #Pickling
                pickle.dump(models, fp)
        update.message.reply_text(mark+'\n')
        update.message.reply_text('\n'.join(sorted(models)))
    else:
        update.message.reply_text('"'+mark+'" такой марки не существует')
    return ConversationHandler.END


def new_cars(update, context):
    update.message.reply_text('Введите название интересующей марки\nДля подсказки введите /marks')
    return MARK_NEW


def find_correct(mark, marks):
    for some_mark in marks:
        if mark.lower() in some_mark.lower():
            return some_mark
        if translit(mark.lower(), 'ru', reversed=True) in some_mark.lower():
            return some_mark
    return mark


def new_get_mark(update, context):
    mark = update.message.text
    with open("marks.txt", "rb") as fp:   # Unpickling
        marks = pickle.load(fp)
    mark = find_correct(mark, marks)
    context.user_data['mark'] = mark
    if mark in marks:
        update.message.reply_text('Введите название интересующей мoдели\nДля подсказки введите /models')
        return MODEL_NEW
    else:
        update.message.reply_text('"'+mark+'" такой марки не существует')
        return ConversationHandler.END


def new_get_number(update, context):
    number = update.message.text
    try:
        number = int(number)
        mark = context.user_data['mark']
        model = context.user_data['model']
        update.message.reply_text('Ищу {} {}'.format(mark, model))
        cars = stats.get_new_stats(mark, model)
        if len(cars)==0:
            update.message.reply_text('Пока недоступно')
        else:
            for car in cars[:min(len(cars), number)]:
                msg = '\n'.join([car[key] for key in car])
                update.message.reply_text(msg)
    except Exception as e:
        print(e)
        update.message.reply_text('Введено не число!!!')
    return ConversationHandler.END


def new_get_model(update, context):
    model = update.message.text
    mark = context.user_data['mark']
    try:
        with open("models/{}.txt".format(mark), "rb") as fp:   # Unpickling
            models = pickle.load(fp)
        model = find_correct(model, models)
        context.user_data['model'] = model
        if model in models:
            update.message.reply_text('Введите число автомобилей для показа')
            return PRICES_NEW
        else:
            update.message.reply_text('"'+mark+' '+model+'" такой модели не существует')
        return ConversationHandler.END
    except Exception as e:
        print(e)
        update.message.reply_text('Поищите данную модель через /models')
        return ConversationHandler.END


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("marks", list_marks))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('models', list_models)],

        states={
            MODEL: [MessageHandler(Filters.text & ~Filters.command, get_models)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    conv_handler_new = ConversationHandler(
        entry_points=[CommandHandler('new', new_cars)],

        states={
            MARK_NEW: [MessageHandler(Filters.text & ~Filters.command, new_get_mark)],
            MODEL_NEW: [MessageHandler(Filters.text & ~Filters.command, new_get_model)],
            PRICES_NEW: [MessageHandler(Filters.text & ~Filters.command, new_get_number)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler_new)
    schedule1.every().day.at("00:00").do(auto_ru_parcer.update_new)
    schedule1.run_continuously(interval=1)
    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
