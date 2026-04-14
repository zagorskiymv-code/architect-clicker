import os
import json
import sqlite3
import re
import time
from functools import wraps
from flask import Flask, request, jsonify, session, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

# ===== КОНФИГ =====
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")
ACCESS_CODE = os.environ.get("ACCESS_CODE", "ILOVEVIBECODING_COMMUNITY")
DB_PATH = os.environ.get("DB_PATH", "game.db")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
MIN_PASSWORD_LENGTH = 6

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS saves (
        user_id INTEGER PRIMARY KEY,
        state_json TEXT NOT NULL DEFAULT '{}',
        dp_total REAL NOT NULL DEFAULT 0,
        dp_max REAL NOT NULL DEFAULT 0,
        last_save INTEGER NOT NULL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ===== ДЕКОРАТОР АВТОРИЗАЦИИ =====
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


# ===== ЭНДПОИНТЫ =====
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/me")
@login_required
def me():
    return jsonify({"username": session["username"]})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    access_code = data.get("access_code", "")
    
    if not username or not password or not access_code:
        return jsonify({"error": "missing fields"}), 400
    
    if not USERNAME_REGEX.match(username):
        return jsonify({"error": "Имя пользователя должно быть 3-20 символов: латиница, цифры, подчёркивание"}), 400
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": "Пароль должен быть минимум 6 символов"}), 400
    
    if access_code != ACCESS_CODE:
        return jsonify({"error": "Неверный код доступа. Обратитесь к архитектору"}), 403
    
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return jsonify({"error": "Имя пользователя уже занято"}), 409
    
    password_hash = generate_password_hash(password)
    cursor = db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    user_id = cursor.lastrowid
    
    # Используем INSERT с IF NOT EXISTS
    db.execute(
        """INSERT OR IGNORE INTO saves (user_id, state_json, dp_total, dp_max, last_save) 
        VALUES (?, '{}', 0, 0, 0)""",
        (user_id,)
    )
    db.commit()
    
    return jsonify({"ok": True})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return jsonify({"error": "missing fields"}), 400
    
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Неверное имя пользователя или пароль"}), 401
    
    session["user_id"] = row["id"]
    session["username"] = row["username"]
    return jsonify({"ok": True, "username": row["username"]})


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"ok": True})


# ===== КОНФИГ СУЩНОСТЕЙ ДЛЯ РАСЧЕТА ДОХОДА =====
ENTITIES_CONFIG = [
    { "id": "tk", "baseRate": 0.1 },
    { "id": "tv", "baseRate": 1 },
    { "id": "iv", "baseRate": 8 },
    { "id": "api", "baseRate": 47 },
    { "id": "ms", "baseRate": 260 },
    { "id": "domain", "baseRate": 1400 },
    { "id": "platform", "baseRate": 7800 },
    { "id": "ecosystem", "baseRate": 44000 }
]


def calculateDpPerSecFromState(state_data):
    """Расчёт DP в секунду из состояния"""
    total = 0
    upgrades = state_data.get("upgrades", [])
    
    adrMul = 2 if "adr" in upgrades else 1
    devopsMul = 2 if "devops" in upgrades else 1
    apiMul = 3 if "contract" in upgrades else 1
    msMul = 3 if "mesh" in upgrades else 1
    platMul = 3 if "platformeng" in upgrades else 1
    uekMul = 2 if "uek" in upgrades else 1
    dkaMul = 2 if "dka" in upgrades else 1
    
    baseGlobal = adrMul * devopsMul
    
    entities = state_data.get("entities", {})
    for cfg in ENTITIES_CONFIG:
        e = entities.get(cfg["id"], {"owned": 0})
        rate = cfg["baseRate"] * e.get("owned", 0) * baseGlobal
        if cfg["id"] == "iv":
            rate *= uekMul * dkaMul
        if cfg["id"] == "api":
            rate *= apiMul
        if cfg["id"] == "ms":
            rate *= msMul
        if cfg["id"] == "platform":
            rate *= platMul
        total += rate
    return max(0, total)


@app.route("/api/load")
@login_required
def load_game():
    db = get_db()
    row = db.execute(
        "SELECT state_json, last_save FROM saves WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()
    
    if not row:
        return jsonify({"state": None})
    
    try:
        state = json.loads(row["state_json"])
    except (ValueError, TypeError):
        return jsonify({"state": None})
    
    if not state or state == {}:
        return jsonify({"state": None})
    
    # Вычисляем время отсутствия и начисляем DP
    last_save = row["last_save"] or 0
    if last_save > 0:
        current_time = int(time.time() * 1000)
        time_diff_ms = current_time - last_save
        
        # Начисляем DP только если пропустил более 10 секунд
        if time_diff_ms > 10000:
            dp_per_sec = calculateDpPerSecFromState(state)
            time_diff_sec = time_diff_ms / 1000.0
            earned = dp_per_sec * time_diff_sec
            
            # Добавляем к текущему DP
            current_dp = float(state.get("dp", 0))
            state["dp"] = current_dp + earned
            
            # Показываем уведомление о начислении
            state["offline_bonus"] = { 
                "earned": earned, 
                "rate": dp_per_sec, 
                "time_sec": round(time_diff_sec, 1) 
            }
    
    return jsonify({"state": state})


@app.route("/api/save", methods=["POST"])
@login_required
def save_game():
    data = request.get_json(silent=True)
    if not data or "state" not in data:
        return jsonify({"error": "missing state"}), 400
    
    state = data["state"]
    if not isinstance(state, dict):
        return jsonify({"error": "state must be object"}), 400
    
    dp = state.get("dp", 0)
    try:
        dp = float(dp)
        if dp < 0:
            dp = 0
    except (ValueError, TypeError):
        return jsonify({"error": "invalid dp"}), 400
    
    # Берём timestamp из состояния (может быть установлен при загрузке)
    last_save = state.get("last_save", 0)
    
    # Если last_save не задан, используем текущее время
    if last_save == 0:
        last_save = int(time.time() * 1000)
    
    state_str = json.dumps(state)
    
    db = get_db()
    db.execute("""
    INSERT INTO saves (user_id, state_json, dp_total, dp_max, last_save, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id) DO UPDATE SET
    state_json = excluded.state_json,
    dp_total = excluded.dp_total,
    dp_max = MAX(dp_max, excluded.dp_total),
    last_save = excluded.last_save,
    updated_at = CURRENT_TIMESTAMP
    """, (session["user_id"], state_str, dp, dp, last_save))
    
    db.commit()
    
    return jsonify({"ok": True})


@app.route("/api/leaderboard")
def leaderboard():
    db = get_db()
    rows = db.execute('''
        SELECT u.username, s.dp_max, s.updated_at
        FROM saves s
        INNER JOIN users u ON u.id = s.user_id
        WHERE s.dp_max > 0
        ORDER BY s.dp_max DESC
        LIMIT 10
    ''').fetchall()
    
    top = [
        {
            "username": row["username"],
            "dp": row["dp_max"],
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]
    return jsonify({"top": top})


# ===== ОБРАБОТКА ОШИБОК =====
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception("Unhandled exception")
    return jsonify({"error": "internal server error"}), 500


# ===== ЗАПУСК =====
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
