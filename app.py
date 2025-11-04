from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

# === Khởi tạo Flask app ===
app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-in-production'  # ĐỔI KEY NÀY TRONG PRODUCTION

# === Cấu hình Flask-Login ===
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# === User Class ===
class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name

# === Giả lập database người dùng ===
users = {
    "admin@skylineimex.com": {"password": "admin123", "name": "Admin Skyline", "id": 1}
}

# === Load user ===
@login_manager.user_loader
def load_user(user_id):
    for email, data in users.items():
        if str(data["id"]) == user_id:
            return User(data["id"], email, data["name"])
    return None

# === Trang chủ - Yêu cầu đăng nhập ===
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html', user=current_user)

# === Trang đăng nhập ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in users and users[email]["password"] == password:
            user = User(users[email]["id"], email, users[email]["name"])
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'danger')

    return render_template('login.html')

# === Đăng xuất ===
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# === Chạy app - QUAN TRỌNG: CHO PHÉP TẤT CẢ HOST + PORT 10000 ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render dùng PORT từ env
    app.run(host='0.0.0.0', port=port, debug=False)
