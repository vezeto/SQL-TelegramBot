import threading
import time
import telebot
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import schedule
from database import Database
import logging
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot import types, TeleBot
from telebot.custom_filters import AdvancedCustomFilter
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup  # States
# States storage
from telebot.storage import StateMemoryStorage

from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialization
state_storage = StateMemoryStorage()  # you can initialize here another storage
bot = telebot.TeleBot(os.getenv('TOKEN'), parse_mode=None, state_storage=state_storage)
db_name = 'users.db'

# Connecting to database or creating new one
db_global = Database()
db_global.create_table()
db_global.close()


# States group
class SubStates(StatesGroup):
    # Just name variables differently
    name = State()  # creating instances of State class is enough from now
    mode = State()
    period = State()
    date = State()


# Class for keeping info about subs
class SubscriptionInfo:
    def __init__(self, user_id, username=None, first_name=None, last_name=None, chat_id=None,
                 sub_name=None, sub_mode=None, period=None, date=None):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.chat_id = chat_id
        self.sub_name = sub_name
        self.sub_mode = sub_mode
        self.period = period
        self.date = date


# global variable
users_subscription_info = {}


# Handler of /cancel
@bot.message_handler(state="*", commands=['cancel'])
def handle_cancel_command(message):
    global users_subscription_info

    chat_id = message.chat.id

    markup = types.ReplyKeyboardRemove()
    # Checking whether we have info about this user
    if chat_id in users_subscription_info:
        del users_subscription_info[chat_id]
        bot.send_message(chat_id, "The subscription operation has been canceled.", reply_markup=markup)
    else:
        bot.send_message(chat_id, "There is no active subscription operation to cancel", reply_markup=markup)
    bot.delete_state(message.from_user.id, message.chat.id)


# Handler of /newsub
@bot.message_handler(commands=['new_sub'])
def handle_newsub_command(message):
    global users_subscription_info  # users_subscription_info as global
    db = Database()

    subscription_info = SubscriptionInfo(message.from_user.id, message.from_user.username, message.from_user.first_name,
                                         message.from_user.last_name, message.chat.id)
    users_subscription_info[message.chat.id] = subscription_info

    if not db.in_users(message.from_user.id):
        db.add_user(subscription_info)

    db.close()

    bot.set_state(message.from_user.id, SubStates.name, message.chat.id)
    bot.send_message(message.chat.id, 'Enter the name of the subscription to the service')


# Next step: getting sub's name
@bot.message_handler(state=SubStates.name)
def handle_subscription_name(message):
    global users_subscription_info  # subscription_info as global

    current_sub_info = users_subscription_info[message.chat.id]
    current_sub_info.sub_name = message.text
    bot.set_state(message.from_user.id, SubStates.mode, message.chat.id)
    bot.send_message(message.chat.id, 'Choose the subscription mode', reply_markup=generate_subscription_keyboard())


# Generating buttons
def generate_subscription_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2)  # one_time_keyboard=True ?
    markup.add(types.KeyboardButton('Yearly'), types.KeyboardButton('Monthly'))
    markup.add(types.KeyboardButton('Weekly'), types.KeyboardButton('Custom'))
    return markup


# Next step: getting sub's mode
@bot.message_handler(state=SubStates.mode, text=['Yearly', 'Monthly', 'Weekly'])
def handle_subscription_mode(message):
    global users_subscription_info
    current_sub_info = users_subscription_info[message.chat.id]

    current_sub_info.sub_mode = message.text
    markup = types.ReplyKeyboardRemove()  # Hide buttons

    bot.set_state(message.from_user.id, SubStates.date, message.chat.id)
    msg_by_bot = 'Enter last date of payment in YYYY-MM-DD format'
    bot.send_message(message.chat.id, text=msg_by_bot, reply_markup=markup)


@bot.message_handler(state=SubStates.mode, text=['Custom'])
def handle_custom_mode(message):
    global users_subscription_info
    current_sub_info = users_subscription_info[message.chat.id]

    current_sub_info.sub_mode = message.text
    markup = types.ReplyKeyboardRemove()
    msg_by_bot = 'Enter custom period of your subscription'
    bot.set_state(message.from_user.id, SubStates.period, message.chat.id)
    bot.send_message(message.chat.id, text=msg_by_bot, reply_markup=markup)


# If user didn't choose one of given options
@bot.message_handler(state=SubStates.mode)
def handle_incorrect_mode(message):
    msg_by_bot = 'Please select one of the available options.\nOr enter /cancel to cancel operation'
    bot.send_message(message.chat.id, text=msg_by_bot)


# Next step: getting sub's period
@bot.message_handler(state=SubStates.period, is_digit=True)
def handle_subscription_period(message):
    global users_subscription_info
    current_sub_info = users_subscription_info[message.chat.id]

    current_sub_info.period = int(message.text)

    bot.set_state(message.from_user.id, SubStates.date, message.chat.id)
    msg_by_bot = 'Enter last date of payment in YYYY-MM-DD format'
    bot.send_message(message.chat.id, text=msg_by_bot)


# If user entered string instead of number
@bot.message_handler(state=SubStates.period, is_digit=False)
def handle_incorrect_period(message):
    msg_by_bot = 'Please enter a valid number.\nOr enter /cancel to cancel operation'
    bot.send_message(message.chat.id, text=msg_by_bot)


# Next step: getting sub's date
@bot.message_handler(state=SubStates.date)
def handle_subscription_date(message):
    global users_subscription_info
    db = Database()
    current_sub_info = users_subscription_info[message.chat.id]

    try:
        current_sub_info.date = datetime.strptime(message.text, "%Y-%m-%d").date()
        db.add_sub(current_sub_info)
        msg_by_bot = 'Your subscription was successfully added!'
        bot.send_message(message.chat.id, text=msg_by_bot)
        bot.delete_state(message.from_user.id, message.chat.id)
    except ValueError:
        msg_by_bot = 'Sorry, there was an error.\nPlease enter the date in the format YYYY-MM-DD.' \
                     '\nOr enter /cancel to cancel operation'
        bot.send_message(message.chat.id, text=msg_by_bot)


# Handler of /start, /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = '''
Hello! Welcome to our subscription management bot!
With this bot, you can easily track your subscriptions and receive notifications about upcoming renewals :)
'''

    bot.reply_to(message, text=welcome_msg)


@bot.message_handler(commands=['list_subs'])
def show_list_subs(message):
    subs_to_show = get_all_subs(message.from_user.id)
    msg_by_bot = ''
    for sub in subs_to_show:
        msg_by_bot += f'{sub[2]}, mode: {sub[3]}, date: {sub[5]}\n'

    bot.send_message(message.chat.id, text=msg_by_bot)


@bot.message_handler(commands=['in_users'])
def check_in_users(message):
    db = Database()
    checker = db.in_users(message.from_user.id)

    db.close()
    if checker:
        msg_by_bot = 'You were found in the database!'
        bot.send_message(message.chat.id, text=msg_by_bot)
    else:
        msg_by_bot = 'You were not found in the database'
        bot.send_message(message.chat.id, text=msg_by_bot)


@bot.message_handler(commands=['delete_user'])
def delete_user_from_db(message):
    db = Database()
    db.delete_user(message.from_user.id)

    db.close()

    msg_by_bot = 'You were removed from the database'
    bot.send_message(message.chat.id, text=msg_by_bot)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    print(message.text)
    bot.send_message(message.chat.id, message.text + ' ' + str(message.from_user.id) + ' ' + message.from_user.username)


# Get all user's subscriptions
def get_all_subs(user_id):
    db = Database()
    subs = db.list_subs(user_id)
    db.close()
    return subs


def check_and_send_notifications():
    print('doing task...', datetime.now)


# schedule.every().day.at('09:00').do(task)

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.add_custom_filter(custom_filters.TextMatchFilter())

bot.infinity_polling()
