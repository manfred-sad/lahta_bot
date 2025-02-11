import requests
import os
import time
import logging
from colorlog import ColoredFormatter
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


last_message_time = None
msg_sleep = 0 #не используется 
msg = True
ticket = False
i = 1

def log(log_file='out.log'):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, 'logs')

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)
    # Форматтер для файла
    file_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)d [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Ротация файла
    file_handler = TimedRotatingFileHandler(
        log_file_path, 
        when='midnight',  # Ротация каждый день в полночь
        interval=1,  # Ротация происходит каждый день
        backupCount=30,  # Количество резервных файлов
        encoding='utf-8',  # Кодировка файла
        delay=False,  # Откладывать открытие файла до первой записи в журнал
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Форматтер для консоли
    console_formatter = ColoredFormatter(
        '%(log_color)s%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',  # Белый цвет для отладочного уровня
            'INFO':     'green',  # Зеленый цвет для информационного уровня
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red,bg_white',
            'asctime':  'green',  # Зеленый цвет для времени
            'levelname': 'green'   # Зеленый цвет для названия уровня лога (INFO)
        }
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

logger = log()

def send_telegram_message(message):
    
    bot_token = '8124405995:AAHX6Pm5JcM-QmpMUNc-bSu7rSrECfZxzs8' #тут надо свои значения добавить
    #chat_id = "@lahta_tickets" #и ID своего чата
    chat_id = "55792067"
    global last_message_time
    current_time = datetime.now()

    if last_message_time is None or (current_time - last_message_time).total_seconds() >= msg_sleep: #так как msg_sleep = 0, то данное условие всегда верно. просто функция стандартна для разных ботов.
        try:
            message_send = requests.Session()
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            params = {
                'chat_id': chat_id,
                'parse_mode': 'html',
                'text': message,
                'disable_web_page_preview': True 
            }
            res = message_send.post(url, params=params)

            if res.status_code == 200:
                response_data = res.json()
                message_id = response_data['result']['message_id']
                logger.info(f"message_id: {message_id}")
                last_message_time = current_time
                logger.info(f"Telegram message sent successfully. Status {res.status_code}.")
                #msg_sleep = 600

            else:
                logger.error(f"Failed to send Telegram message. Status {res.status_code}. Text: {res.text}")
        except Exception as e:

            logger.error("Error sending Telegram message: ", exc_info=True)
    else:
        logger.info("Message not sent (too soon).")

def check_slots(i):
    global msg
    global ticket
    global msg_sleep
    url = "https://tickets.lakhta.events/api/no-scheme"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru,fi;q=0.9,it;q=0.8,ko;q=0.7,fr;q=0.6,en;q=0.5,tr;q=0.4,de;q=0.3,pt;q=0.2,el;q=0.1",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": "LAKHTA_CENTRE_ONLINE_TICKETS=27dfdhg2dnhqkhhij3bg809u6p",
        "Origin": "https://tickets.lakhta.events",
        "Referer": "https://tickets.lakhta.events/event/23FA307410B1F9BE84842D1ABE30D6AB48EA2CF8/2025-02-08",
        "Sec-Ch-Ua": '"Chromium";v="130", "YaBrowser";v="24.12", "Not?A_Brand";v="99", "Yowser";v="2.5"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"
    }

    payload = {
        "hash": "23FA307410B1F9BE84842D1ABE30D6AB48EA2CF8"
    }

    while True:
        try:
            logger.info(f"Try #{i}")
            response = requests.post(url, json=payload, headers=headers)
            log_message = ""  #формируем строку с данными, для удобного логирования

            if response.status_code == 200:
                response_json = response.json()
                available_dates = response_json.get("response", {}).get("calendar", [])

                message = "<b>🎫 Появились билеты:\n</b>" 
                found_tickets = False  

                for date_entry in available_dates:
                    date = date_entry["day"]
                    times = date_entry["_time"]

                    available_slots = [
                        f"{slot['time']} ({slot['quantity']})"
                        for slot in times if int(slot["quantity"]) > 0
                    ]

                    if available_slots: #если есть доступные билеты, формируем отформатированные данные для отправки в телегу
                        found_tickets = True
                        message += f"<b>{date}</b>\n"
                        message += ", ".join(available_slots)
                        message += "\n\n"

                        log_message += f"{date}: " + ", ".join(available_slots) + "; "

                if found_tickets and msg:
                    message += "<a href='https://tickets.lakhta.events/event/23FA307410B1F9BE84842D1ABE30D6AB48EA2CF8/'> <b>Купить на официальном сайте</b></a>"
                    send_telegram_message(message)  
                    logger.info("sent tg msg TICKETS AVAILABLE")
                    msg = False 
                    ticket = True 

                elif not found_tickets and ticket:
                    message = "❌ <b>Билеты закончились!</b>"
                    send_telegram_message(message)
                    logger.info("sent tg msg ALL GONE")
                    msg = True 
                    ticket = False 
                    logger.info("Sleep 0.5 hours before new try")
                    time.sleep(600) 
                    # тупая задержка 10 минут, чтоб не спамить о единичных билетах, которые не оплатили, и которые вернулись в пул
                    # TODO придумать алгоритм, который бы пропускал такие возвраты. Может для уведомления нужно больше 3 билетов?
                    # 

                logger.debug(f"Билеты доступны! {log_message}" if found_tickets else "Нет доступных билетов")


            logger.info("Sleep before new try 1 min")
            time.sleep(60)
            i = i + 1

        except Exception as e:
            logger.error(f"Error occurred {e}")
            logger.info("sleep 600")
            time.sleep(600)

if __name__ == "__main__":
    logger.info("Start Cheking tickets")
    check_slots(i) 