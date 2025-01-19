from flask import Flask, request, jsonify
import psycopg2
import random
import threading
import time
from config import *

app = Flask(__name__)

def connect_to_db():   # coonect to bd
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )
    return conn

def remove_code(telephone_number):
    time.sleep(300)
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET code = NULL WHERE telephone_number = %s", (telephone_number,))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/change_code', methods=['POST'])
def change_code():
    data = request.json
    telephone_number = data.get('telephone_number')
    passwd = data.get('passwd')

    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("SELECT passwd FROM "+table_name_users+" WHERE telephone_number = %s", (telephone_number,))
    result = cursor.fetchone()

    if result is None:
        return jsonify({"message": "Wrong password"}), 401

    stored_passwd = result[0]
    
    if stored_passwd != passwd:
        return jsonify({"message": "Wrong password"}), 401

    code = random.randint(10000, 99999)

    cursor.execute("UPDATE "+table_name_users+" SET code = %s WHERE telephone_number = %s", (code, telephone_number))
    conn.commit()

    threading.Thread(target=remove_code, args=(telephone_number,), daemon=True).start()

    cursor.close()
    conn.close()

    return jsonify({"message": "Code change successful"}), 200

if __name__ == '__main__':
    app.run(debug=True)
