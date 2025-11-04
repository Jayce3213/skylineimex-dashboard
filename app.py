from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from playwright.sync_api import sync_playwright
import os
from datetime import datetime

# === Flask App ===
app = Flask(__name__)
app.secret_key = 'skylineimex-secret-key-2025'

# === Login Manager ===
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# === User Class ===
class User(UserMixin):
    def __init__(self, id, email, name, quota=999):
        self.id = id
        self.email = email
        self.name = name
        self.quota = quota

# === Giả lập DB users ===
users = {
    1: {"email": "admin@skylineimex.com", "password": "admin123", "name": "Admin Skyline"}
}

@login_manager.user_loader
def load_user(user_id):
    user_id = int(user_id)
    if user_id in users:
        u = users[user_id]
        return User(user_id, u["email"], u["name"], u.get("quota", 999))
    return None

# === TRADEATLAS CONFIG ===
TRADE_USER = os.environ.get('TRADE_USER', 'kalimacompany01@gmail.com')
TRADE_PASS = os.environ.get('TRADE_PASS', 'Kalima01')

# === Hàm scrape TradeAtlas ===
def scrape_tradeatlas(query='0901', limit=10):
    data = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Login
            page.goto("https://www.tradeatlas.com/en/login")
            page.fill("input[name='email']", TRADE_USER)
            page.fill("input[name='password']", TRADE_PASS)
            page.click("button:has-text('Login')")
            page.wait_for_load_state("networkidle")
            
            if "login" in page.url.lower():
                browser.close()
                return {"error": "Login failed"}
            
            # Search
            search_url = f"https://www.tradeatlas.com/en/shipment-multiple?hs={query}"
            page.goto(search_url)
            page.wait_for_selector("table", timeout=10000)
            
            rows = page.query_selector_all("table tr")
            for i, row in enumerate(rows[:limit]):
                cells = row.query_selector_all("td")
                if len(cells) >= 6:
                    data.append({
                        "date": cells[0].inner_text().strip() if len(cells) > 0 else "N/A",
                        "hs_code": query,
                        "product": cells[2].inner_text().strip() if len(cells) > 2 else "N/A",
                        "buyer": cells[3].inner_text().strip() if len(cells) > 3 else "N/A",
                        "supplier": cells[4].inner_text().strip() if len(cells) > 4 else "N/A",
                        "quantity": cells[5].inner_text().strip() if len(cells) > 5 else "N/A",
                        "amount": cells[6].inner_text().strip() if len(cells) > 6 else "$0",
                        "country": "VN → AE"  # Mặc định
                    })
            
            browser.close()
    except Exception as e:
        return {"error": str(e)}
    
    return data

# === Routes ===
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        for uid, u in users.items():
            if u["email"] == email and u["password"] == password:
                user = User(uid, email, u["name"], u.get("quota", 999))
                login_user(user)
                return redirect(url_for('index'))
        
        flash('Sai email hoặc mật khẩu!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# === API Tìm kiếm TradeAtlas ===
@app.route('/api/search')
@login_required
def search():
    if current_user.quota <= 0:
        return {"error": "Hết quota!"}, 403
    
    query = request.args.get('q', '0901')
    data = scrape_tradeatlas(query)
    
    if "error" in data:
        return data, 500
    
    # Giả lập quota
    users[current_user.id]["quota"] -= 1
    
    return {"data": data, "total": len(data)}
@app.route('/search')
@login_required
def search_page():
    return render_template('search.html', user=current_user)
# === Chạy app ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
