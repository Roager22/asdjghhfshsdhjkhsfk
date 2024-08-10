import telebot
import json
import os
import requests
from requests.exceptions import Timeout, RequestException
from parser import AvitoParser
from utils import get_user_files


# Загрузка конфигурации из файла
def load_config():
    with open('config.json') as file:
        return json.load(file)


config = load_config()
TOKEN = config['TOKEN']

bot = telebot.TeleBot(TOKEN)
parser_instances = {}  # Для хранения экземпляров парсера по user_id
user_states = {}  # Словарь для отслеживания состояния пользователей


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        'Установить URL',
        'Установить ключевые слова',
        'Установить максимальную цену',
        'Установить минимальную цену',
        'Установить гео',
        'Установить время парсинга',
        'Установить время отдыха',
        'Установить максимальное количество страниц',
        'Установить Chat ID для Telegram',
        'Начать парсинг',
        'Остановить парсинг'
    ]
    keyboard.add(*buttons)
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=keyboard)
    user_states[message.chat.id] = 'awaiting_action'


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if state == 'awaiting_action':
        actions = {
            'Установить URL': 'awaiting_url',
            'Установить ключевые слова': 'awaiting_keywords',
            'Установить максимальную цену': 'awaiting_max_price',
            'Установить минимальную цену': 'awaiting_min_price',
            'Установить гео': 'awaiting_geo',
            'Установить время парсинга': 'awaiting_parsing_time',
            'Установить время отдыха': 'awaiting_rest_time',
            'Установить максимальное количество страниц': 'awaiting_max_pages',
            'Установить Chat ID для Telegram': 'awaiting_chat_id',
            'Начать парсинг': 'start_parsing',
            'Остановить парсинг': 'stop_parsing'
        }

        if message.text in actions:
            if actions[message.text] == 'start_parsing':
                start_parsing(message)
            elif actions[message.text] == 'stop_parsing':
                stop_parsing(message)
            else:
                user_states[user_id] = actions[message.text]
                bot.send_message(message.chat.id, f'Пожалуйста, введите значение для: {message.text}')
        else:
            bot.send_message(message.chat.id, 'Неизвестная команда. Пожалуйста, выберите действие из меню.')

    elif state and state.startswith('awaiting_'):
        handlers = {
            'awaiting_url': set_url,
            'awaiting_keywords': set_keywords,
            'awaiting_max_price': set_max_price,
            'awaiting_min_price': set_min_price,
            'awaiting_geo': set_geo,
            'awaiting_parsing_time': set_parsing_time,
            'awaiting_rest_time': set_rest_time,
            'awaiting_max_pages': set_max_pages,
            'awaiting_chat_id': set_chat_id
        }

        if state in handlers:
            handlers[state](message)
            user_states[user_id] = 'awaiting_action'
        else:
            bot.send_message(message.chat.id, 'Неизвестное состояние. Пожалуйста, выберите действие из меню.')


def set_url(message):
    url = message.text
    update_settings('url', url, message.chat.id)
    bot.send_message(message.chat.id, f'URL сохранен: {url}')


def set_keywords(message):
    keywords = message.text
    update_settings('keywords', keywords, message.chat.id)
    bot.send_message(message.chat.id, f'Ключевые слова сохранены: {keywords}')


def set_max_price(message):
    try:
        max_price = int(message.text)
        update_settings('max_price', max_price, message.chat.id)
        bot.send_message(message.chat.id, f'Максимальная цена сохранена: {max_price}')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректное значение для максимальной цены.')


def set_min_price(message):
    try:
        min_price = int(message.text)
        update_settings('min_price', min_price, message.chat.id)
        bot.send_message(message.chat.id, f'Минимальная цена сохранена: {min_price}')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректное значение для минимальной цены.')


def set_geo(message):
    geo = message.text
    update_settings('geo', geo, message.chat.id)
    bot.send_message(message.chat.id, f'Гео сохранено: {geo}')


def set_parsing_time(message):
    try:
        parsing_time = int(message.text)
        update_settings('parsing_time', parsing_time, message.chat.id)
        bot.send_message(message.chat.id, f'Время парсинга сохранено: {parsing_time}')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректное значение для времени парсинга.')


def set_rest_time(message):
    try:
        rest_time = int(message.text)
        update_settings('rest_time', rest_time, message.chat.id)
        bot.send_message(message.chat.id, f'Время отдыха сохранено: {rest_time}')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректное значение для времени отдыха.')


def set_max_pages(message):
    try:
        max_pages = int(message.text)
        update_settings('max_pages', max_pages, message.chat.id)
        bot.send_message(message.chat.id, f'Максимальное количество страниц сохранено: {max_pages}')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректное значение для максимального количества страниц.')


def set_chat_id(message):
    chat_id = message.text
    update_settings('chat_id', chat_id, message.chat.id)
    bot.send_message(message.chat.id, f'Chat ID сохранен: {chat_id}')


def update_settings(key, value, user_id):
    settings_file = get_user_files(user_id)['settings']
    if os.path.isfile(settings_file):
        with open(settings_file, 'r') as file:
            settings = json.load(file)
    else:
        settings = {}
    settings[key] = value
    with open(settings_file, 'w') as file:
        json.dump(settings, file, indent=4)


def start_parsing(message):
    user_id = message.chat.id
    if user_id in parser_instances:
        bot.send_message(user_id, 'Парсинг уже запущен.')
        return

    user_files = get_user_files(user_id)
    settings_file = user_files['settings']

    if os.path.isfile(settings_file):
        with open(settings_file, 'r') as file:
            settings = json.load(file)

        parser = AvitoParser(user_id=user_id)  # Передаем user_id в конструктор
        parser.url = settings.get('url', '')
        parser.keywords = settings.get('keywords', '').split(',')
        parser.max_price = int(settings.get('max_price', 0))
        parser.min_price = int(settings.get('min_price', 0))
        parser.geo = settings.get('geo', '')
        parser.parsing_time = int(settings.get('parsing_time', 120))
        parser.rest_time = int(settings.get('rest_time', 10))
        parser.max_pages = int(settings.get('max_pages', 5))
        parser.chat_id = settings.get('chat_id', '')

        # Подключаем сигналы
        parser.update_log.connect(lambda msg: send_telegram_message(parser.chat_id, msg))
        parser.finished.connect(lambda: send_telegram_message(parser.chat_id, 'Парсинг завершён'))
        parser_instances[user_id] = parser
        parser.start()

        bot.send_message(user_id, 'Парсинг начат.')
    else:
        bot.send_message(user_id, 'Настройки не найдены.')


def stop_parsing(message):
    user_id = message.chat.id
    if user_id in parser_instances:
        parser = parser_instances[user_id]
        parser.stop()
        del parser_instances[user_id]
        bot.send_message(user_id, 'Парсинг остановлен.')
    else:
        bot.send_message(user_id, 'Парсинг не запущен.')


def send_telegram_message(chat_id, text):
    bot_token = config['TOKEN']
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    try:
        response = requests.post(url, data={'chat_id': chat_id, 'text': text}, timeout=10)
        response.raise_for_status()
    except (Timeout, RequestException) as e:
        print(f'Ошибка при отправке сообщения в Telegram: {e}')


# Запуск бота
try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f'Ошибка: {e}')
