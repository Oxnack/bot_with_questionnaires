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

def hash_text(text):
    sha256 = hashlib.sha256()
    sha256.update(text.encode('utf-8'))
    return sha256.hexdigest()

def generate_random_string(length=5):  # for deeplink code
    characters = string.ascii_letters + string.digits  
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

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


############################################  DATABASE ###########

def connect_to_db():   # coonect to db
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )
    return conn

def edit_row_users(tg_id, phone_number):  # EDIT row for table USERS
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE ' + str(table_name_users) + ' SET tg_id = %s WHERE phone_number = %s', (tg_id, phone_number))
        conn.commit()
    conn.close()

def find_row_by_tg_id_users(telegram_id):   # FIND row for table BY TG_ID  USERS
    conn = connect_to_db()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM users WHERE tg_id = %s", (telegram_id,))
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

def add_row_messages(tg_id):   # ADD row in MESSAGES
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO messages (tg_id) VALUES (%s) RETURNING id;", (tg_id,))  
        returned_id = cursor.fetchone()[0]
        conn.commit()
        print('now id message: ' + str(returned_id))
        return returned_id
    conn.close()

def add_row_users(tg_id):   # ADD row IN messages
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO users (tg_id, rule) VALUES (%s, %s) RETURNING id;", (str(tg_id), "user"))  # ADD row in USERS (rule = user)
        conn.commit()
        print("new user with id: " + str(tg_id))
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

def edit_row_users_change_rule(rule, tg_id):  # EDIT row for table USERS (rule_change)
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE ' + str(table_name_users) + ' SET rule = %s WHERE tg_id = %s', (rule, tg_id))
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
