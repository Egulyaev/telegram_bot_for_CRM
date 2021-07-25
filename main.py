import json
import logging
import os
import time
from datetime import datetime, timedelta

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'http://127.0.0.1:8000/api/tickets/'
STATUS = {
    'open': 'Заявка открыта',
    'in_work': 'Заявка взята в работу',
    'pending': 'Выполнение заявки приостановлено',
    'done': 'Выполнено'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
    filemode='w'
)


def parse_ticket_status(ticket):
    try:
        ticket_status = STATUS[ticket['status']]
        ticket_text = ticket['ticket_text']
        ticket_id = ticket ['id']
    except KeyError:
        logging.error('Ошибка значения ключа')
        return 'Ошибка значения ключа'
    return f'Изменился статус работ по обращению "ID: {ticket_id} Обращение: {ticket_text}"!\n\n{ticket_status}'


def get_ticket_status(current_timestamp):
    headers = {'Authorization': f'{API_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            API_URL,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException as e:
        logging.error('Ошибка соединения с сервером')
        raise e
    try:
        return homework_statuses.json()
    except json.decoder.JSONDecodeError as e:
        logging.error('Ошибка декодирования JSON')
        raise e


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = Bot(token=TELEGRAM_TOKEN)
    logging.debug('Бот запущен')
    current_timestamp = datetime.now()
    while True:
        try:
            tickets = get_ticket_status(current_timestamp)
            for ticket in range(len(tickets)):
                str_upd_date = tickets[ticket]['updated']
                upd_date = datetime.strptime(f'{str_upd_date}', '%Y-%m-%dT%H:%M:%S.%fZ')
                upd_date = upd_date + timedelta(minutes=180)
                if upd_date > current_timestamp:
                    send_message(
                        parse_ticket_status(
                            tickets[ticket]),
                        bot_client
                    )
                    logging.info('Отправлено сообщение')
            current_timestamp = datetime.now() - timedelta(seconds=1)
            time.sleep(10)

        except Exception as e:
            logging.error(f'Бот столкнулся с ошибкой: {e}')
            try:
                send_message(f'Бот столкнулся с ошибкой: {e}', bot_client)
            except telegram.error.Unauthorized:
                logging.error('Ошибка авторизации бота')
            except telegram.error.BadRequest:
                logging.error('Ошибка запроса телеграмм')
            time.sleep(5)


if __name__ == '__main__':
    main()
