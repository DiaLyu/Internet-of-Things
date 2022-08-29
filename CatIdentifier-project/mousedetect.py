import mouse  # Для работы с мышью
import cv2  # OpenCV - для анализа фото
import datetime as dt  # Для получения текущего времени
import os  # Для работы с путями
import time  # Для выстановки задержек
from pygame import mixer  # Используется для проигрывания музыки
from threading import Thread  # Для телеграм-бота
import telebot  # Для работы с телеграм-ботом
import logging #логгер

logging.basicConfig(filename="app.log", filemode="w", format="%(asctime)s:%(levelname)s - %(levelname)s - %(message)s", level=logging.INFO)

def get_platform_independed_path(*args):
    root = os.getcwd()
    for string in args:
        root = os.path.join(root, string)
    #print(root) //debug
    return root

# Делает снимок с подключённой камеры
def get_photo():
    # Включаем камеру
    cap = cv2.VideoCapture(0)
    # "Прогреваем" камеру, чтобы снимок не был тёмным
    for i in range(15):
        cap.read()
    # Делаем снимок
    ret, frame = cap.read()
    # Отключаем камеру
    cap.release()
    logging.info("Сделал снимок")
    return frame

# Анализирует фото на наличие кошки
def analyse_photo(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.01, minNeighbors=5)
    return faces, len(faces) > 0

# Сигнализация
def alert(frame, faces, now):
    logging.info("Тревога! запустил аудио.")
    mixer.init()
    mixer.music.load(get_platform_independed_path("alert.mp3"))
    mixer.music.play()
    catTracked = True
    for x, y, w, h in faces:
        frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
    # cv2.imshow("Alert", frame)
    # cv2.waitKey()
    pictureName = str(now) + ".png"
    cv2.imwrite(get_platform_independed_path(
        "Archive", "Alert", pictureName), frame)
    logging.info("Сохранил фото в архив.")
    send_alert_bot()

# Обработка ложной тревоги


def restore_after_fake_alert(frame, now):
    pictureName = str(now) + ".png"
    cv2.imwrite(get_platform_independed_path(
        "Archive", "FakeAlert", pictureName), frame)
    logging.info("Ложное срабатывание.")

# обновить chatId


def update_chatId():
    with open(get_platform_independed_path("chatId.txt"), 'r') as fp:
        chatId = int(fp.read())
        logging.info("Прочитал chatId из файла")
    return chatId


# инициализация бота
chatId = update_chatId()
telegramToken = None
with open(get_platform_independed_path("telegramToken.txt"), 'r') as fp:
    telegramToken = str(fp.read())
    logging.info("Прочитал TelegramToken из файла")
bot = telebot.TeleBot(telegramToken, parse_mode=None)
# обработчик сообщений для бота


@bot.message_handler(commands=['яглавный', 'пишимне', "start"])
def send_welcome(message):
    chatId = message.chat.id
    bot.reply_to(
        message, "Теперь вы мой хозяин. Если я кого-то постороннего увижу, то буду писать именно вам!")
    with open(get_platform_independed_path("chatId.txt"), 'w') as fp:
        fp.write(str(chatId))
    logging.info("Пришла заявка на смену chatId.\nЗаменил chatId.")


# Отправить уведомления о тревоге через бота
def send_alert_bot():
    chatId = update_chatId()
    bot.send_message(chatId, "Коты у компьютера!")
    logging.info("Сообщил о тревоге")


# инициализация
face_cascade = cv2.CascadeClassifier(
    get_platform_independed_path("cat_face.xml"))
pos = mouse.get_position()
mouseMoved = False

# Запускаем бота в отдельный поток.
t = Thread(target=bot.polling)
t.daemon = True
t.start()

# Основной цикл
while True:
    # Проверяем триггер на срабатывание
    logging.info("В исходном состоянии.")
    while not mouseMoved:
        bufPos = mouse.get_position()
        if(bufPos != pos):
            mouseMoved = True
    # Дата+время
    now = dt.datetime.now()
    print(str(now) + " : триггер сработал. Проверяем...")

    frame = get_photo()
    # Проверяем, сделан ли был снимок
    if(not frame.any()):
        print("Камера не обнаружена, программа прекращает работу.")
        logging.critical("Камера не обнаружена. Программа прекращает работу.")
        break
    # Записываем в файл
    cv2.imwrite(get_platform_independed_path("LastPhoto.jpg"), frame)
    faces, catDetected = analyse_photo(frame)
    if(catDetected):
        print(str(now) + " : Кошачий обнаружен! Принимаются меры.")
        alert(frame, faces, now)
    else:
        print(str(now) + " : Ложное срабатывание.")
        restore_after_fake_alert(frame, now)
    logging.info("Программа уходит в сон на 15 секунд.")
    print("Программа вернётся в исходное положение через 15 сек...")
    time.sleep(15)
    pos = mouse.get_position()
    mouseMoved = False
