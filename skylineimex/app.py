# app.py - SKYLINE IMEX DASHBOARD (ĐÃ SỬA LỖI)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3

app = Flask(__name__)
app.secret_key = 'skylineimex2025'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, name, quota):
        self.id = id
        self.email = email
        self.name = name
        self.quota = quota

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('xnk.db')
    c = conn.cursor()
    c.execute("SELECT id, email, name, quota FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return User(*row) if row else None

def init_db():
    conn = sqlite3.connect('xnk.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT, quota INTEGER)''')
    c.execute("INSERT OR IGNORE INTO users (email, password, name, quota) VALUES (?, ?, ?, ?)",
              ('admin@skylineimex.com', 'admin123', 'Admin', 999))
    conn.commit()
    conn.close()
init_db()

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd = request.form['password']
        conn = sqlite3.connect('xnk.db')
        c = conn.cursor()
        c.execute("SELECT id, email, name, quota FROM users WHERE email=? AND password=?", (email, pwd))
        user = c.fetchone()
        conn.close()
        if user:
            login_user(User(*user))
            return redirect(url_for('index'))
        flash('Sai email hoặc mật khẩu!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.email != 'admin@skylineimex.com':
        return "Chỉ admin mới được phép!", 403
    if request.method == 'POST':
        conn = sqlite3.connect('xnk.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (email, password, name, quota) VALUES (?, ?, ?, ?)",
                      (request.form['email'], request.form['password'], request.form['name'], request.form['quota']))
            conn.commit()
            flash('Tạo tài khoản thành công!')
        except sqlite3.IntegrityError:
            flash('Email đã tồn tại!')
        conn.close()
    return render_template('add_user.html')

@app.route('/api/search')
@login_required
def search():
    if current_user.quota <= 0:
        return {"error": "Hết lượt tìm kiếm!"}, 403
    # Giả lập dữ liệu
    data = [
        {"date": "2024-08-31", "hs_code": "090111", "product": "Cà phê Arabica", "buyer": "AN THỊ LỆ",
         "supplier": "CÔNG TY TNHH", "quantity": "20 TNE", "amount": 16284512, "purpose_country": "UAE"}
    ]
    # Trừ quota
    conn = sqlite3.connect('xnk.db')
    c = conn.cursor()
    c.execute("UPDATE users SET quota = quota - 1 WHERE id=?", (current_user.id,))
    conn.commit()
    conn.close()
    return data

if __name__ == '__main__':
    app.run(debug=True)