import os
import sqlite3

DB_PATH = 'game.db'

# Удаляем старую базу
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Создаём новую пустую базу
conn = sqlite3.connect(DB_PATH)
conn.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.execute('''
CREATE TABLE saves (
    user_id INTEGER PRIMARY KEY,
    state_json TEXT NOT NULL DEFAULT '{}',
    dp_total REAL NOT NULL DEFAULT 0,
    dp_max REAL NOT NULL DEFAULT 0,
    last_save INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
''')
conn.commit()
conn.close()

print("✅ База данных очищена и создана заново!")
print("👥 Все пользователи удалены")
print("🏆 Доска Лидеров пуста")
print("🎮 Игра готова к демонстрации!")
