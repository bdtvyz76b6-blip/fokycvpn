import sqlite3
from datetime import datetime, timedelta

DB = "fokyc.db"


def connect():
    return sqlite3.connect(DB)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '',
        first_name TEXT DEFAULT '',
        tariff TEXT DEFAULT 'Нет подписки',
        subscription_until TEXT DEFAULT '',
        subscription_link TEXT DEFAULT '',
        trial_used INTEGER DEFAULT 0,
        notify INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        days INTEGER,
        stars INTEGER,
        status TEXT DEFAULT 'paid',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY,
        days INTEGER
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username="", first_name=""):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (user_id, username, first_name)
    VALUES (?, ?, ?)
    """, (user_id, username or "", first_name or ""))

    cur.execute("""
    UPDATE users
    SET username = ?, first_name = ?
    WHERE user_id = ?
    """, (username or "", first_name or "", user_id))

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result


def get_all_users():
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users ORDER BY created_at DESC"
    )

    result = cur.fetchall()
    conn.close()

    return result


def get_user_ids():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users")
    result = [x[0] for x in cur.fetchall()]

    conn.close()
    return result


def activate_subscription(
    user_id,
    days,
    link,
    tariff="👑 Fokyc VPN"
):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT subscription_until FROM users WHERE user_id = ?",
        (user_id,)
    )

    row = cur.fetchone()
    now = datetime.now()

    if row and row[0]:
        try:
            until = datetime.fromisoformat(row[0])
            if until < now:
                until = now
        except Exception:
            until = now
    else:
        until = now

    until += timedelta(days=days)

    cur.execute("""
    UPDATE users
    SET tariff = ?,
        subscription_until = ?,
        subscription_link = ?
    WHERE user_id = ?
    """, (
        tariff,
        until.isoformat(),
        link,
        user_id
    ))

    conn.commit()
    conn.close()

    return until


def activate_trial(user_id, days, link):
    conn = connect()
    cur = conn.cursor()

    until = datetime.now() + timedelta(days=days)

    cur.execute("""
    UPDATE users
    SET tariff = ?,
        subscription_until = ?,
        subscription_link = ?,
        trial_used = 1
    WHERE user_id = ?
    """, (
        "🎁 Пробный период",
        until.isoformat(),
        link,
        user_id
    ))

    conn.commit()
    conn.close()

    return until


def trial_used(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT trial_used FROM users WHERE user_id = ?",
        (user_id,)
    )

    row = cur.fetchone()
    conn.close()

    return bool(row and row[0])


def add_payment(user_id, days, stars):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO payments
    (user_id, days, stars, status)
    VALUES (?, ?, ?, 'paid')
    """, (user_id, days, stars))

    conn.commit()
    conn.close()


def add_promo(code, days):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO promocodes
    (code, days)
    VALUES (?, ?)
    """, (code.upper(), days))

    conn.commit()
    conn.close()


def get_promo(code):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT code, days FROM promocodes WHERE code = ?",
        (code.upper(),)
    )

    result = cur.fetchone()
    conn.close()

    return result


def delete_promo(code):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM promocodes WHERE code = ?",
        (code.upper(),)
    )

    conn.commit()
    conn.close()


def get_expired_users():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT user_id
    FROM users
    WHERE subscription_until != ''
      AND subscription_until < ?
    """, (datetime.now().isoformat(),))

    result = [x[0] for x in cur.fetchall()]

    conn.close()
    return result