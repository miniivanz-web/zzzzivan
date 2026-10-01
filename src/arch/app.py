from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'tvoja_super_sekretnaja_kluch_fraza_2026'

def get_db_connection():
    try:
        return mysql.connector.connect(
            host="185.114.247.43",
            port=3306,
            database="sch688_vvedenie",
            user="sch688_vvedenie",
            password="Qwerty123"
        )
    except Error as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

@app.route('/user_register', methods=['POST'])
def user_register():
    req = request.get_json()
    if not req or 'name' not in req or 'email' not in req or 'password' not in req:
        return jsonify({'status': 'error', 'message': 'Не все данные переданы'}), 400

    name = req['name']
    login = req['email']
    password = req['password']

    password_hash = generate_password_hash(password)

    cnx = get_db_connection()
    if not cnx:
        return jsonify({'status': 'error', 'message': 'Ошибка БД'}), 500

    cur = cnx.cursor()
    try:
        cur.execute('SELECT id FROM users WHERE email = %s', (login,))
        if cur.fetchone():
            return jsonify({'status': 'error', 'message': 'Пользователь с таким Email уже существует'}), 409

        cur.execute('INSERT INTO `users`(`username`, `email`, `password_hash`) VALUES (%s, %s, %s)',
                    (name, login, password_hash))
        cnx.commit()
    except Error as e:
        cnx.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cur.close()
        cnx.close()

    return jsonify({'status': 'ok', 'message': 'Регистрация успешна'})

@app.route('/user_login', methods=['POST'])
def user_login():
    req = request.get_json()
    if not req or 'username' not in req or 'password' not in req:
        return jsonify({'status': 'error', 'message': 'Не все данные переданы'}), 400

    login = req['username']
    password = req['password']

    cnx = get_db_connection()
    if not cnx:
        return jsonify({'status': 'error', 'message': 'Ошибка БД'}), 500

    cur = cnx.cursor(dictionary=True)
    try:
        cur.execute('SELECT id, username, email, password_hash FROM users WHERE email = %s', (login,))
        user = cur.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return jsonify({'status': 'ok', 'redirect': '/dashboard'})
        else:
            return jsonify({'status': 'error', 'message': 'Неверный логин или пароль'}), 401
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cur.close()
        cnx.close()

@app.route('/dashboard')
def dashboard():
    # Проверяем, залогинен ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
def registration():
    return render_template('registration.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route('/api/transfer', methods=['POST'])
def make_transfer():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Не авторизован'}), 401

    data = request.get_json()
    recipient = data.get('recipient')
    amount = data.get('amount')
    comment = data.get('comment', '')

    if not recipient or not amount:
        return jsonify({'status': 'error', 'message': 'Не хватает данных'}), 400

    # Здесь должна быть логика:
    # 1. Проверить баланс пользователя в БД
    # 2. Проверить существование получателя
    # 3. Начать транзакцию в БД: списать у отправителя, зачислить получателю
    # 4. Записать обе операции в таблицу transactions

    print(f"Пользователь {session['user_id']} переводит {amount} руб. на {recipient}. Коммент: {comment}")

    return jsonify({'status': 'ok', 'message': 'Перевод успешно выполнен'})

if __name__ == '__main__':
    app.run(debug=True)
