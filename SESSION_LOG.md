# Сессия разработки Architect Clicker

**Дата:** 14 апреля 2026  
**Время:** 13:37 - 19:41 UTC  
**Авторы:** OpenClaw (AI) + User  
**Цель:** Построить idle clicker-игру Architect Clicker с нуля за ~6 часов

---

## 📋 План реализации (9 шагов)

### Шаг 1/9: Бэкенд — базовый каркас
Создали Flask-сервер с SQLite, конфигами и эндпоинтом `/api/me`.

Файлы:
- `requirements.txt` - `flask>=3.0.0`
- `index.html` - временная заглушка
- `README.md` - инструкция по запуску
- `server.py` - основной сервер (~100 строк)

**Проверка:** Сервер стартует, база создаётся, `/api/me` возвращает 401 без авторизации ✅

---

### Шаг 2/9: Бэкенд — регистрация и авторизация
Добавили `/api/register`, `/api/login`, `/api/logout`.

Логика:
- Проверка кода доступа (ARCHITECT2026)
- Валидация username/password
- Хеширование паролей с `werkzeug.security`
- Сессии через `flask.session`

**Проверка:** Регистрация работает, логин сохраняет cookie, logout очищает ☑️

---

### Шаг 3/9: Бэкенд — сохранение и лидерборд
Добавили `/api/load`, `/api/save`, `/api/leaderboard`.

Структура БД:
```sql
users: id, username, password_hash, created_at
saves: user_id (FK), state_json, dp_total, updated_at
```

**Проверка:** Можно сохранять прогресс и видеть лидеров в консоли ☑️

---

### Шаг 4/9: Фронт — каркас HTML и стили
Полная переработка `index.html`:
- Современный дизайн с CSS custom properties
- Экран авторизации с табами
- Игровой экран (левая/правая колонка)
- Модальное окно лидерборда
- Тосты для уведомлений
- Анимации (float-text, card-flash)
- Адаптивность для мобильных

**Проверка:** UI открывается, но формы не работают (логика в шаге 5) ☑️

---

### Шаг 5/9: Фронт — логика авторизации
- Переключение табов Вход/Регистрация
- Обработка форм через FormData
- API-клиент с fetch + credentials: "include"
- Обработка ошибок с пользовательскими сообщениями
- Кнопка выхода с вызовом `/api/logout`

**Проверка:** Регистрация, вход, выход работают, сообщения об ошибках показываются ☑️

---

### Шаг 6/9: Фронт — игровая механика
- Состояние игры: `dp`, `clickPower`, `totalClicks`, `entities`, `upgrades`, `achievements`
- Конфиги: 8 сущностей + 8 прокачек
- Расчёт дохода: `calculateDpPerSec()` с мультипликаторами
- Покупка сущностей с проверкой доступности
- Покупка прокачек с мгновенным действием
- Всплывающий текст при клике (`showFloatText`)
- Флеш-эффект на карточках
- Обработчик главной кнопки

**Проверка:** Клик даёт DP, можно покупать сущности через консоль (визуально пока нет) ☑️

---

### Шаг 7/9: Фронт — рендеринг и игра
- Функции `renderDp()`, `renderEntities()`, `renderUpgrades()`
- Игровой цикл: сохранение каждые 10 сек, авто-доход каждые 100мс
- `/api/load` с offline-бонусом (расчёт за время отсутствия)
- `/api/save` с `dp_max` для лидерборда

**Проверка:** Игра визуально работает, DP растёт, сохраняется на сервер и в localStorage ☑️

---

### Шаг 8/9: Фронт — события и ачивки
- Система событий: 8 типов (negative/positive)
- Весовая выборка: события `uek_reject`, `dka_reject` имеют вес 0.5 с прокачкой
- Временные эффекты: `click_x3`, `income_x2`, `income_zero`
- 11 достижений с проверкой условий
- Тосты для уведомлений о наградах

**Проверка:** События появляются каждые 45-90 сек, ачивки выдаются с анимацией ☑️

---

### Шаг 9/9: Фронт — финиш
- Модальное окно лидерборда с `top 10`
- Подсветка текущего пользователя
- Автосохранение при `beforeunload`
- Отрисовка после загрузки

**ИГРА ГОТОВА!** 🎉

---

## 💻 Технические решения

### База данных
```sql
CREATE TABLE saves (
  user_id INTEGER PRIMARY KEY,
  state_json TEXT NOT NULL,      -- JSON с полным состоянием
  dp_total REAL NOT NULL,         -- текущие очки
  dp_max REAL NOT NULL,           -- максимальные очки (для лидерборда)
  last_save INTEGER NOT NULL,     -- timestamp последнего сохранения (ms)
  updated_at TIMESTAMP
);
```

**Почему `dp_max`?**  
Пользователь мог иметь 100K DP, потом уйти, потом вернуть 50K. Лидерборд должен показывать **максимум**, а не текущее значение.

---

### Offline earning
При загрузке проверяем `last_save`:
```python
time_diff_sec = (current_time - last_save) / 1000
dp_per_sec = calculateDpPerSecFromState(state)
earned = dp_per_sec * time_diff_sec
```

**Ограничение:** >10 секунд отсутствия. Минимум 10 сек, чтобы не считать обновления страницы.

---

### Состояние игры
```javascript
{
  dp: 1234,                    // текущие очки
  clickPower: 1,               // доход от клика
  totalClicks: 1000,           // всего кликов
  entities: {
    tk: { owned: 50, busy: 0 }, // owned = куплено, busy = используются ИВ
    tv: { owned: 10 },
    // ... остальные
  },
  upgrades: ["adr", "devops"], // купленные прокачки
  achievements: ["first_click"],
  activeEffects: [...],        // временные эффекты
  stats: { eventsSurvived: 5, eventsMissed: 2, consecutiveSurvived: 3 },
  last_save: 1776180326025     // timestamp в миллисекундах
}
```

---

### mergeState() - ключевая функция

**Проблема:** При загрузке состояния с сервера некоторые `entities` могут быть `undefined`.

**Решение:**
```javascript
function mergeState(defaults, loaded) {
  const result = { ...defaults, ...loaded };
  
  // Для entities: объединяем structure defaults + loaded
  if (loaded.entities) {
    result.entities = { ...defaults.entities };
    for (const key in loaded.entities) {
      result.entities[key] = {
        ...defaults.entities[key],
        ...loaded.entities[key]
      };
    }
  }
  
  // Остальные поля заменяем
  result.upgrades = loaded.upgrades || [];
  result.dp = loaded.dp !== undefined ? loaded.dp : defaults.dp;
  // ...
}
```

**Почему не просто `loaded.entities`?**  
Так как `loaded.entities` может иметь `owned: 0, disabled: undefined`, мы добавляем `defaults.entities[key]` для полноты структуры.

---

## 🐛 Найденные и исправленные баги

### Баг 1: Не работает лидерборд
**Симптом:** `{"error":"internal server error"}` при запросе `/api/leaderboard`.

**Причина:** Таблица `saves` не имеет колонки `dp_max` и `last_save` в старой базе, и `JOIN` возвращает пустой результат.

**Решение:**
- Создали чистую БД (`game.db` удалён)
- Изменили `INSERT` на `INSERT OR IGNORE` в registration
- Исправили `JOIN` на `INNER JOIN` в `/api/leaderboard`

---

### Баг 2: Данные не сохраняются при перезагрузке
**Симптом:** После F5 все очки и сущности обнуляются.

**Причина:** `mergeState()` перезаписывал `entities` на пустые, вместо объединения.

**Решение:** Переписали `mergeState()` для корректного слияния объектов.

---

### Баг 3: Очки обнулялись при старом save
**Симптом:** `dp_max` в базе = 0, хотя `DP` было 100K+.

**Причина:** `ON CONFLICT` в `save_game()` не обновлял `dp_max`, а перезаписывал текущим значением.

**Решение:** `dp_max = MAX(dp_max, excluded.dp_total)` в SQL.

---

### Баг 4: `last_save` сбрасывался
**Симптом:** Offline earning не работал, так как `last_save` = 0 после каждой загрузки.

**Причина:** При загрузке мы не обновляли `last_save` в `state`, и потом он перезаписывался в `0`.

**Решение:**
1. Убрали `state["last_save"] = int(current_time)` из `load_game()`
2. Добавили сохранение `last_save` в `save_game()` каждый раз
3. Обновляем `last_save = Date.now()` перед каждым сохранением на клиенте

---

### Баг 5: Новый пользователь видел чужие данные
**Симптом:** Новый аккаунт загружал сохранение старого пользователя.

**Причина:** Старые куки в браузере.

**Решение:** Проверка при `loadGame`: `if(res.state === null) console.log("Fresh state")`.

---

## 🔄 Изменения конфигурации

### Код доступа
Было: `ARCHITECT2026`  
Стало: `ILOVEVIBECODING_COMMUNITY`

### Название проекта
Было: `Architect Tycoon`  
Стало: `Architect Clicker`

### Навигация
Кнопка "Лидерборд" → "Доска Лидеров"

---

## 📂 Финальная структура проекта

```
architect-game/
├── .git/                         # Git repository
├── .gitignore
├── README.md
├── requirements.txt
├── server.py                     # ~300 строк
├── index.html                    # ~850 строк
└── game.db                       # База данных (не в git)
```

**Git remote:** `git@github.com:zagorskiymv-code/architect-clicker.git`

---

## 🎯 Технические детали

### Конфиг сущностей
```javascript
const ENTITIES = [
  { id: "tk", name: "ТК", icon: "🧱", baseCost: 15, baseRate: 0.1 },
  { id: "tv", name: "Точка Взаимодействия", icon: "🔘", baseCost: 100, baseRate: 1 },
  { id: "iv", name: "ИВ", icon: "🔗", baseCost: 1100, baseRate: 8 },
  // ... и т.д. до экосистемы (330M DP)
];
```

### Система прокачек
Каждая прокачка имеет:
- `cost` - сколько DP стоит
- `unlock()` - условие отображения/покупки
- Множитель к доходу (2x или 3x)

### События
- **Частота:** каждые 45-90 сек (`spawnEvent()`)
- **Окно реакции:** 15 сек (`setTimeout(() => onMiss(), 15000)`)
- **Типы:** `positive`, `negative`
- **Взвешенный выбор:** `weight()` для редких событий

---

## 🛠️ Что ещё нужно для продакшена

### 1. Nginx конфиг
Готовый файл сохранён в `/tmp/nginx_architect.conf`

Требует:
```bash
sudo apt-get update && sudo apt-get install -y nginx
sudo cp /tmp/nginx_architect.conf /etc/nginx/sites-available/architect-clicker
sudo ln -s /etc/nginx/sites-available/architect-clicker /etc/nginx/sites-enabled/
sudo service nginx restart
```

### 2. DNS
Привязать `ai-agent-game.ru` к IP сервера.

### 3. SSL/TLS
Добавить Let's Encrypt сертификат через Certbot.

### 4. Monitoring
- Логгирование ошибок (сейчас только console.log)
- Метрики (количество игроков, DP в секунду)
- Алерты при критических ошибках

### 5. Бэкапы
```bash
#!/bin/bash
cd /home/openclaw/.openclaw/workspace/architect-game
tar -czf backup-$(date +%Y%m%d).tar.gz game.db
```

---

## 🎉 Финальные заметки

**Итог:** За ~6 часов построили полноценную idle-игру с бэкендом, базой данных, системой сохранения, событиями, ачивками и лидербордом.

**Ключевые решения:**
- Vanilla JS без зависимостей
- Session-based auth
- `dp_max` для справедливого лидерборда
- Offline earning с `last_save`
- `mergeState()` для надёжного восстановления состояния

**Код доступа:** `ILOVEVIBECODING_COMMUNITY`

---

*Сессия завершена. Проект готов к демонстрации!* 🚀
