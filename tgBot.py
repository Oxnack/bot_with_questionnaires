from config import *
import telebot
from telebot import types
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import random
import os
import string
from psycopg2 import sql
import json
from flask import Flask, request, jsonify
import re
import threading
import io


bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/send_message', methods=['POST'])   #{"passwd":"", "message":"", "user_ids":["",""...]}
def send_message():
    print("func http send")
    data = request.get_json()

    if not data or 'user_ids' not in data or 'message_id' not in data or 'passwd' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    user_ids = data['user_ids']
    message_id = data['message_id']
    passwd = data['passwd']

    passwd = hash_text(passwd)

    if passwd == reqestPass_hash: #-----check passwd
        row_data = find_row_by_id_messages(message_id)
        if row_data:
            message = row_data["message"]
            buttons_json = row_data["buttons"]
            filenames = list(map(str, row_data["image"].split()))
            id = row_data["id"]
            mp4_files = get_mp4_files(filenames)
            jpg_files = get_jpg_files(filenames)
            print(message, buttons_json, filenames)

            buttons = None
            if buttons_json != None: 
                buttons = extract_button_names_from_json(buttons_json)
            

            for user_id in user_ids:  
                try:              # start point to send? add buttons....
                    keyboard = types.InlineKeyboardMarkup()
                    if (buttons != None):
                        for button in buttons:
                            keyboard.add(types.InlineKeyboardButton(button, callback_data=(button + "_///next_id_message///_" + str(id))))
                    
                    
                    if (mp4_files != None):
                        if not mp4_files:
                            print("No video")
                        
                        for video in mp4_files:
                            with open(video, 'rb') as video_file:
                                bot.send_video(user_id, video_file)

                    
                    if (jpg_files != None and jpg_files != []):
                        media = []
        
                        for filename in jpg_files:
                            if os.path.exists(filename):
                                with open(filename, 'rb') as photo:
                                    photo_data = io.BytesIO(photo.read())
                                    photo_data.name = os.path.basename(filename) 
                                    media.append(telebot.types.InputMediaPhoto(photo_data))
                        if media:
                          #  bot.send_media_group(user_id, media, )
                           #bot.send_paid_media(user_id, caption=message, star_count=0, media=media)
                            bot.send_media_group(user_id, media=media )
                            bot.send_message(user_id, message, reply_markup=keyboard)
                    
                    else:
                        bot.send_message(user_id, message, reply_markup=keyboard)
                    


                    print(f'Message sent to {user_id}')

                except Exception as e:
                    print(f'Failed to send message to {user_id}: {e}')
        else:
            print("bad num message in db ----------[-]")
            return jsonify({'status': 'Error: Bad message id'})

        return jsonify({'status': 'Messages sent'}), 200
    else:
        return jsonify({'status': 'access denied, wrong password'}), 200

def hash_text(text):
    sha256 = hashlib.sha256()
    sha256.update(text.encode('utf-8'))
    return sha256.hexdigest()

def get_mp4_files(file_list):
    return [file for file in file_list if file.endswith('.mp4') and os.path.isfile(file)]

def get_jpg_files(file_list):
    return [file for file in file_list if file.endswith('.jpg') and os.path.isfile(file)]

def extract_button_names_from_json(json_string):
    try:
        data = json.loads(json_string)
        button_names = [key for key in data.keys()]
        return button_names
    except json.JSONDecodeError:
        print("Err: Bad format JSON")
        return []
    
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    button_name = call.data
    button_text, message_id = extract_text_and_id(button_name)
    print(button_name, button_text, message_id)

    if (button_text != None and message_id != None):
      #  bot.answer_callback_query(call.id, "Вы нажали Кнопку 1")
       # bot.send_message(call.message.chat.id, "Вы выбрали ответ: " + button_text)
        data_message = find_row_by_id_messages(message_id)
        buttons_json = data_message["buttons"]
        message = data_message["message"]
        new_data_buttons, added = add_id_to_json_array(data_message["buttons"], button_text, call.message.chat.id)
        edit_buttons_message(message_id, new_data_buttons)

        buttons = None
        if buttons_json != None: 
            buttons = extract_button_names_from_json(buttons_json)
        keyboard = types.InlineKeyboardMarkup()
        if (buttons != None):
            for button in buttons:
                if (button == button_text):
                    if added == True:
                        keyboard.add(types.InlineKeyboardButton(button + " ✅", callback_data=(button + "_///next_id_message///_" + str(message_id))))
                    else:
                        keyboard.add(types.InlineKeyboardButton(button, callback_data=(button + "_///next_id_message///_" + str(message_id))))
                else:
                    if is_user_select_answer(button, call.message.chat.id, buttons_json):
                        keyboard.add(types.InlineKeyboardButton(button + " ✅", callback_data=(button + "_///next_id_message///_" + str(message_id))))
                    else:
                        keyboard.add(types.InlineKeyboardButton(button, callback_data=(button + "_///next_id_message///_" + str(message_id))))

        if (button_text == "Другое" and added == True):
            bot.reply_to(call.message, "Вы выбрали ответ Другое, введите свой ответ (только текст)")
            user_states[str(call.message.chat.id) + "_message_id"] = message_id
            user_states[str(call.message.chat.id)] = STATE_WAITING_FOR_ANOTHER_ANSWER_MESSAGE
        elif (button_text == "Другое" and added == False):
            bot.reply_to(call.message, "Вы удалили свой ответ")
        try:
            bot.edit_message_text(message, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
        except Exception as e:
            print("err to edit message")

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_ANOTHER_ANSWER_MESSAGE)
def another_answer_handler(message):
    answer = message.text
    message_id = user_states.get(str(message.chat.id) + "_message_id")
    message_row = find_row_by_id_messages(message_id)
    user_id = message.chat.id
    json_text = message_row["buttons"]
    new_json_buttons = json_another_answer_add(user_id, json_text, answer)
    edit_buttons_message(message_id, new_json_buttons)

    bot.send_message(message.chat.id, "Хорошо, ваш ответ записан")

    user_states.pop(str(message.chat.id) + "_message_id", None)
    user_states.pop(str(message.chat.id), None)

def json_another_answer_add(user_id, json_text, answer):
    data = json.loads(json_text)
    
    if "Другое" in data:
        if str(user_id) in data["Другое"]:
            del data["Другое"][str(user_id)]
        
        data["Другое"][str(user_id)] = answer
        
        return json.dumps(data)
    
    return json_text

def add_id_to_json_array(json_string, name, id_value): # out: json, bool
    data = json.loads(json_string)
    
    if name in data:
        if name == "Другое":
            if str(id_value) in data[name]:
                del data[name][str(id_value)]
                return json.dumps(data), False  
            else:
                data[name][str(id_value)] = ""
                return json.dumps(data), True 
        if id_value in data[name]:
            data[name].remove(id_value) 
            return json.dumps(data), False  
        else:
            data[name].append(id_value)  
            return json.dumps(data), True  
    else:
        print("err: no this answer in json")



def extract_text_and_id(input_string):
    separator_index = input_string.find('_///next_id_message///_')
    
    if separator_index != -1:
        text = input_string[:separator_index].strip() 
        message_id = input_string[separator_index + len('_///next_id_message///_'):].strip() 
        return text, int(message_id)
    else:
        return None, None

def is_user_select_answer(answer, user_id, json_text):
    data = json.loads(json_text)
    
    if answer in data:
        return user_id in data[answer]
    
    return False

user_states = {}

STATE_WAITING_FOR_PHONE = 'waiting_for_phone'    # Autorisation stats
STATE_WAITING_FOR_CODE = 'waiting_for_code'

STATE_WAITING_FOR_TEXT_MESSAGE = 'waiting_for_text_message' # Curator stats
STATE_WAITING_FOR_IMAGE_MESSAGE = 'waiting_for_image_message'
STATE_WAITING_FOR_BUTTONS_MESSAGE = 'waiting_for_buttons_message'
STATE_WAITING_FOR_ANOTHER_ANSWER_MESSAGE = 'waiting_for_another_answer_message'

@bot.message_handler(commands=['start']) 
def send_welcome(message):
    data = find_row_by_tg_id_users(str(message.chat.id))
    if data:
        bot.send_message(message.chat.id, "Вы авторизованы:" + str(data))
    else:
        bot.send_message(message.chat.id, "Требуется авторизация: \n отправьте свой номер телефона в формате 89997776655:")
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_PHONE
    
@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_PHONE)
def handle_phone_number(message):
    phone_number = message.text
    bot.reply_to(message, f"Спасибо! Вы ввели номер: {phone_number}, проверяем")
    data = find_row_by_telephone_number_users(phone_number)

    if data:
        bot.send_message(message.chat.id, "Мы нашли вас в базе! введите код регистрации сообщенный куратором (в формате 00000)")
        user_states[str(message.chat.id) + "_phone"] = phone_number
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_CODE
    else:
        bot.send_message(message.chat.id, "К сожалению номер не найден! проверьте и отправьте снова")

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_CODE)
def handle_code(message):
    code = message.text
    bot.send_message(message.chat.id, f"Вы ввели код: {code}. проверяем")

    phone_number = user_states.get(str(message.chat.id) + "_phone")

    data = find_row_by_telephone_number_users(phone_number)

    if data:
        if (code == data["code"]):  # check autorisation code 
            edit_row_users(message.chat.id, phone_number)
            bot.send_message(message.chat.id, "Код верный, вы авторизованы! tgID: " + str(message.chat.id))
    else:
        bot.send_message(message.chat.id, "К сожалению номер не найден! проверьте и отправьте снова")
    user_states.pop(str(message.chat.id), None)
    user_states.pop(str(message.chat.id) + "_phone", None)

########################################################################
@bot.message_handler(commands=['send']) 
def send_message_only_curator(message):
    print("send_message_function")
    data = find_row_by_tg_id_users(str(message.chat.id))
    if (data['is_admin'] == True):       # <<<<<<<<<<<<<<<
        bot.send_message(message.chat.id, "Напишите текст сообщения, без картинок и опроса")
        message_number = add_row_messages(message.chat.id)
        user_states[str(message.chat.id) + "_message_id"] = message_number
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_TEXT_MESSAGE
    else:
        bot.send_message(message.chat.id, "К сожалению вы не куратор")

    
@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_TEXT_MESSAGE)
def handle_text_message(message):
    text = message.text
    user_states[str(message.chat.id) + "_user_now_message_text"] = text
    edit_text_message(user_states.get(str(message.chat.id) + "_message_id"), text)
    bot.send_message(message.chat.id, f"Хорошо, ваше сообщение: \"{text}\", добавлено в базу даннных!")
    bot.send_message(message.chat.id, f"Теперь добавьте картинки к сообщению, отправляйте картинки отдельными сообщеними, после того как закончите отправьте stop или /stop")
    user_states[str(message.chat.id)] = STATE_WAITING_FOR_IMAGE_MESSAGE

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_IMAGE_MESSAGE, content_types= ["photo"])
def handle_photo(message) -> None:
   # print(message)
    print("photo message send")
    if user_states.get(str(message.chat.id) + "_user_now_image_files") == None:
        user_states[str(message.chat.id) + "_user_now_image_files"] = []
    if message.photo:
        
        # bot.send_message(message.chat.id, "Отлично! Теперь добавьте кнопки к своему опросу. Когда закончите добавлять кнопк введите '''stop'''")
        print("[+++]")
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        print(file_info)
        downloaded_file = bot.download_file(file_info.file_path)
        random_filename = generate_random_string()
        user_states.get(str(message.chat.id) + "_user_now_image_files").append(str(random_filename+".jpg"))
        with open(f"{random_filename}.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)

    if message.caption == "stop":
        edit_image_messages(user_states.get(str(message.chat.id) + "_message_id"), user_states.get(str(message.chat.id) + "_user_now_image_files"))
        bot.send_message(message.chat.id, "Хорошо. Теперь добавьте кнопки к своему опросу, каждая кнопка - отдельным сообщением, длина кнопки не более 20 символов. Когда закончите добавлять кнопки введите stop или /stop")
        print("NO PHOTO")
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_BUTTONS_MESSAGE

# @bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_IMAGE_MESSAGE, content_types= ["video"])
# def handle_video(message) -> None:
#    # print(message)
#     print("video message send--")
#     if user_states.get(str(message.chat.id) + "_user_now_image_files") == None:
#         user_states[str(message.chat.id) + "_user_now_image_files"] = []
#     if message.video:
        
#         # bot.send_message(message.chat.id, "Отлично! Теперь добавьте кнопки к своему опросу. Когда закончите добавлять кнопк введите '''stop'''")
#         print("[+++]")
#         fileID = message.video[-1].file_id
#         file_info = bot.get_file(fileID)
#         print(file_info)
#         downloaded_file = bot.download_file(file_info.file_path)
#         random_filename = generate_random_string()
#         user_states.get(str(message.chat.id) + "_user_now_image_files").append(str(random_filename+".jpg"))
#         with open(f"{random_filename}.mp4", 'wb') as new_file:
#             new_file.write(downloaded_file)

#     if message.caption == "stop":
#         edit_image_messages(user_states.get(str(message.chat.id) + "_message_id"), user_states.get(str(message.chat.id) + "_user_now_image_files"))
#         bot.send_message(message.chat.id, "Хорошо. Теперь добавьте кнопки к своему опросу, каждая кнопка - отдельным сообщением, длина кнопки не более 20 символов. Когда закончите добавлять кнопки введите ```stop```")
#         print("NO PHOTO")
#         user_states[str(message.chat.id)] = STATE_WAITING_FOR_BUTTONS_MESSAGE

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_IMAGE_MESSAGE, content_types=["video"])
def handle_video(message) -> None:
    print("video message received--")
    
    if user_states.get(str(message.chat.id) + "_user_now_image_files") is None:
        user_states[str(message.chat.id) + "_user_now_image_files"] = []
  
    if message.video:
        
        fileID = message.video.file_id  
        file_info = bot.get_file(fileID)
        print(file_info)
        
        downloaded_file = bot.download_file(file_info.file_path)
        
        random_filename = generate_random_string()
        
        user_states[str(message.chat.id) + "_user_now_image_files"].append(f"{random_filename}.mp4")
        
        with open(f"{random_filename}.mp4", 'wb') as new_file:
            new_file.write(downloaded_file)

    if message.caption and "stop" in message.caption.lower():
        edit_image_messages(user_states.get(str(message.chat.id) + "_message_id"), user_states.get(str(message.chat.id) + "_user_now_image_files"))
        
        bot.send_message(message.chat.id, "Хорошо. Теперь добавьте кнопки к своему опросу, каждая кнопка - отдельным сообщением, длина кнопки не более 20 символов. Когда закончите добавлять кнопки, введите stop или /stop")
        
        print("NO PHOTO")
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_BUTTONS_MESSAGE


@bot.message_handler(commands=['stop']) 
def send_welcome(message):

    if (user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_IMAGE_MESSAGE):
        edit_image_messages(user_states.get(str(message.chat.id) + "_message_id"), user_states.get(str(message.chat.id) + "_user_now_image_files"))
        
        bot.send_message(message.chat.id, "Хорошо. Теперь добавьте кнопки к своему опросу, каждая кнопка - отдельным сообщением, длина кнопки не более 20 символов. Когда закончите добавлять кнопки, введите stop или /stop")
        
        print("NO PHOTO")
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_BUTTONS_MESSAGE

    elif (user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_BUTTONS_MESSAGE):
        bot.send_message(message.chat.id, f"Вы закончили добавление кнопок к опроснику, ваши кнопки: {str(user_states[str(message.chat.id) + "_user_now_message_buttons"])}")

        db_buttons_json = create_json_from_array(user_states[str(message.chat.id) + "_user_now_message_buttons"])
        edit_buttons_message(user_states.get(str(message.chat.id) + "_message_id"), db_buttons_json)

        user_states.pop(str(message.chat.id), None)
        user_states.pop(str(message.chat.id) + "_user_now_message_text", None)
        user_states.pop(str(message.chat.id) + "_message_id", None)
        user_states.pop(str(message.chat.id) + "_user_now_message_buttons", None)



@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_IMAGE_MESSAGE)
def handle_text_message(message):
    text = message.text
    if text == "stop":
        edit_image_messages(user_states.get(str(message.chat.id) + "_message_id"), user_states.get(str(message.chat.id) + "_user_now_image_files"))
        bot.send_message(message.chat.id, "Хорошо. Теперь добавьте кнопки к своему опросу, каждая кнопка - отдельным сообщением, длина кнопки не более 20 символов. Когда закончите добавлять кнопки введите stop или /stop")
        print("NO PHOTO")
        user_states[str(message.chat.id)] = STATE_WAITING_FOR_BUTTONS_MESSAGE


@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id)) == STATE_WAITING_FOR_BUTTONS_MESSAGE)
def handle_buttons_message(message):
    text = message.text
    if user_states.get(str(message.chat.id) + "_user_now_message_buttons") == None:
        user_states[str(message.chat.id) + "_user_now_message_buttons"] = []

    if text != "stop":
        user_states[str(message.chat.id) + "_user_now_message_buttons"].append(text)
    else:
        bot.send_message(message.chat.id, f"Вы закончили добавление кнопок к опроснику, ваши кнопки: {str(user_states[str(message.chat.id) + "_user_now_message_buttons"])}")

        db_buttons_json = create_json_from_array(user_states[str(message.chat.id) + "_user_now_message_buttons"])
        edit_buttons_message(user_states.get(str(message.chat.id) + "_message_id"), db_buttons_json)

        user_states.pop(str(message.chat.id), None)
        user_states.pop(str(message.chat.id) + "_user_now_message_text", None)
        user_states.pop(str(message.chat.id) + "_message_id", None)
        user_states.pop(str(message.chat.id) + "_user_now_message_buttons", None)



    
#############################################################################

def generate_random_string(length=13):
    characters = string.ascii_letters + string.digits 
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def create_json_from_array(array):
    result = {}

    for item in array:
        result[item] = []
    
    result["Другое"] = {}
    
    json_result = json.dumps(result, ensure_ascii=False, indent=4)
    
    return json_result


def connect_to_db():   # coonect to db
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )
    return conn

def edit_row_users(tg_id, phone_number):  # EDIT row for table 
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE ' + str(table_name_users) + ' SET telegram_id = %s WHERE phone_number = %s', (tg_id, phone_number))
        conn.commit()
    conn.close()

def find_row_by_tg_id_users(telegram_id):   # FIND row for table BY TG_ID
    conn = connect_to_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        row = cursor.fetchone()
        return row
    conn.close()

def find_row_by_telephone_number_users(telephone_number):   # FIND row for table BY TELEPHONE_NUMBER
    conn = connect_to_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM users WHERE phone_number = %s", (telephone_number,))
        row = cursor.fetchone()
        return row
    conn.close()

def add_row_messages(tg_id):   # ADD row IN messages
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO messages (tg_id) VALUES (%s) RETURNING id;", (tg_id,))  
        returned_id = cursor.fetchone()[0]
        conn.commit()
        print('now id message: ' + str(returned_id))
        return returned_id
    conn.close()

def find_row_by_id_messages(id):   # FIND row for table BY ID in messages
    conn = connect_to_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM messages WHERE id = %s", (id,))
        row = cursor.fetchone()
        return row
    conn.close()

def edit_text_message(num, message):       # EDIT text in row IN messages
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE messages SET message = %s WHERE id = %s", (message, num))
        conn.commit()
    conn.close()

def edit_buttons_message(num, buttons_json):       # EDIT buttons in row IN messages|||input: text json buttons
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE messages SET buttons = %s WHERE id = %s", (buttons_json, num))
        conn.commit()
    conn.close()

def edit_image_messages(num, medias):      # EDIT images and videos in MESSAGES --------in raw in images sting with names of files "name1.jpg name2.mp4 name3.jpg"
    if (medias != None and medias != []):
        x = " ".join(medias)

        conn = connect_to_db()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE messages SET image = %s WHERE id = %s", (x, num))
            conn.commit()
        conn.close()


def run_bot():
    bot.polling(none_stop=True)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_bot()



    
def create_table(conn):
    with conn.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS your_table (
                id SERIAL PRIMARY KEY,
                tg_id TEXT NOT NULL,
                data TEXT
            )
        ''')
        conn.commit()

