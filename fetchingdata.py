import psycopg2
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        host=os.getenv("DB_HOST"),
        password=os.getenv("DB_PASSWORD")
    )

def get_or_create_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if user is None:
                cursor.execute("INSERT INTO users (id, status) VALUES (%s, %s) RETURNING id, status", (user_id, True))
                user = cursor.fetchone()

            return user
def get_new_signals(last_check_time):
    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("SELECT * FROM signals WHERE start_date <= %s AND end_date >= %s", (last_check_time.strftime('%Y-%m-%d %H:%M:%S'),last_check_time.strftime('%Y-%m-%d %H:%M:%S'),))
            rows = cursor.fetchall()
            
            new_signals = []
            for row in rows:
                signal = {
                    'id': row[0],
                    'image': row[1],
                    'text': row[2],
                    'start_date': row[3],
                    'end_date': row[4]
                }
                new_signals.append(signal)

            return new_signals
def get_all_unblocked_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE status = %s", (True,))
            rows = cursor.fetchall()

            unblocked_users = []
            for row in rows:
                user = {
                    'id': row[0],
                    'status': row[1],
                    'requested_signal': row[2]
                }
                unblocked_users.append(user)

            return unblocked_users
        
def get_all_requested_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE requested_signal = %s", (True,))
            rows = cursor.fetchall()

            unblocked_users = []
            for row in rows:
                user = {
                    'id': row[0],
                    'status': row[1],
                    'requested_signal': row[2]
                }
                unblocked_users.append(user)

            return unblocked_users
def block_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET status = false WHERE id = %s", (user_id,))


def check_user_status(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT status FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            print(result[0])
            return result[0]
            
def request_signal(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET requested_signal = TRUE WHERE id = %s", (user_id,))
            conn.commit()
def add_signal( text_of_message, dt, de):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO signals (image, text, start_date, end_date) VALUES (123, %s, %s, %s)", ( text_of_message, dt, de))
            conn.commit()
def reset_signal_request(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET requested_signal = FALSE WHERE id = %s", (user_id,))
            conn.commit()

def get_users_who_requested_signals():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE status = TRUE AND requested_signal = TRUE")
            rows = cursor.fetchall()
            unblocked_users = []
            for row in rows:
                user = {
                    'id': row[0],
                    'status': row[1],
                    'requested_signal': row[2]
                }
                unblocked_users.append(user)
            return unblocked_users