import time
from datetime import datetime, timedelta
from typing import List, Dict

import gspread
import telebot
import threading
from oauth2client.service_account import ServiceAccountCredentials

bot: telebot.TeleBot = telebot.TeleBot(
    # token='6380339604:AAFtOjqWgPX7zMIQ2nrBzuBIXR-3lF9gBI8'  # original bot
    token='6426234952:AAFFW03vFQUvu5VYhamtGWwJuvIcfAJ72WM'  # test bot
)

scope: List = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    'sheets_credentials.json', scope
)
gc = gspread.authorize(creds)
spreadsheet = gc.open('surveyResponses')
sheet = spreadsheet.sheet1
users_sheet = spreadsheet.get_worksheet(1)
user_ids = users_sheet.col_values(1)[1:]

reviews_list = []


@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(
            message.chat.id,
            text=f'☺️ Добро пожаловать в бот\n<b>La Esmeralda!</b>\n\n'
                 f'Обратите внимание, что этот бот предназначен только для внутреннего использования, '
                 f'и если у вас нет доступа, вы не сможете им воспользоваться.\n\n'
                 f'🍱 Если вы хотите разместить заказ, пожалуйста, перейдите на наш веб-сайт, '
                 f'или свяжитесь с нами по номеру\n📞 +998 99 - 661 44 44\n\n'
                 f'❤️ Мы будем рады ответить на ваши вопросы и помочь вам.',
            parse_mode='HTML'
        )
    except Exception as err:
        bot.send_message(
            message.chat.id,
            text=f'Ошибка\n\n{err}\n\n'
                 f'Что-то пошло не так, пожалуйста,обратитесь к '
                 f'разработчику со скриншотами/'
        )
        time.sleep(1)


@bot.message_handler(commands=['post'])
def send_message(message):
    if message.chat.id == 368195441:
        new_review = message.text[6:]
        bot.send_message(
            chat_id=-1001507264536,
            text=new_review
        )


def get_latest_record():
    try:
        all_records = sheet.get_all_records()
        if all_records:
            return all_records[-1]
        return None
    except Exception:
        return None


def check_for_changes():
    latest_record = None
    while True:
        try:
            time.sleep(10)
            new_record = get_latest_record()

            if new_record and new_record != latest_record:
                new_time = (datetime.strptime(
                    new_record['Дата отправки'][11:16], '%H:%M') + timedelta(
                    hours=5)).strftime('%H:%M')
                review_format: Dict = {
                    '<b>Дата отправки</b>': new_record['Дата отправки'][:10],
                    '<b>Имя гостья</b>': new_record['Как вас зовут?'],
                    '<b>Телефон гостья</b>': new_record['Какой у вас номер телефона?'],
                    '\n<b>Официант</b>': new_record['Кто вас обслуживал?'],
                    '─ Обслуживание': f"<b>{new_record['Качество обслуживание']} {'✅' if new_record['Качество обслуживание'] else '(Не поставили оценку)'}</b>",
                    '─ Основное блюдо': f"<b>{new_record['Качество основных блюд']} {'✅' if new_record['Качество основных блюд'] else '(Не поставили оценку)'}</b>",
                    '─ Барные напитки': f"<b>{new_record['Качество барных напитков']} {'✅' if new_record['Качество барных напитков'] else '(Не поставили оценку)'}</b>",
                    '─ Десерты': f"<b>{new_record['Качество десертов']} {'✅' if new_record['Качество десертов'] else '(Не поставили оценку)'}</b>",
                    '─ Интерьер': f"<b>{new_record['Качество интерьера']} {'✅' if new_record['Качество интерьера'] else '(Не поставили оценку)'}</b>",
                    '\n<b>Как вы о нас узнали?</b>': new_record['Как вы о нас узнали?'],
                    '<b>Комментарии</b>': new_record['Комментарии'],
                }

                formatted_review = '\n'.join(
                    [f'{key}: {value}' for key, value in review_format.items()]
                )

                bot.send_message(
                    -1001507264536, # RESTAURANT ID
                    text=f'<b>--- Новый отзыв в {new_time}---</b>\n\n'
                         f'{formatted_review}',
                    parse_mode='HTML'
                )

                latest_record = new_record
        except Exception as e:
            bot.send_message(
                368195441,
                f"Error in check_for_changes: {e}"
            )
            time.sleep(1)


def polling_thread():
    while True:
        try:
            print('Bot started')
            bot.infinity_polling(
                timeout=20,
                skip_pending=False,
                long_polling_timeout=20,
                logger_level=40,
                allowed_updates=['message', 'edited_channel_post',
                                 'callback_query'],
                restart_on_change=False,
                path_to_watch=None
            )
        except Exception as e:
            bot.send_message(
                368195441,
                f"Error in check_for_changes: {e}"
            )
            time.sleep(5)


check_thread = threading.Thread(target=check_for_changes)
polling_thread = threading.Thread(target=polling_thread)

check_thread.start()
polling_thread.start()

check_thread.join()
polling_thread.join()
