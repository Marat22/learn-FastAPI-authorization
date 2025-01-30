import sqlite3

conn = sqlite3.connect(r"app.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 0
)
""")

conn.commit()


def get_user_by_username(username: str) -> tuple[int, str, str, str, int]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    return user


def get_user_by_email(email: str) -> tuple[int, str, str, str, int]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    return user


def add_user(username, email, hashed_password):
    conn.execute(
        "INSERT INTO users (username, email, hashed_password, is_active) VALUES (?, ?, ?, ?)",
        (username, email, hashed_password, False),
    )
    conn.commit()


def activate_user(email):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = 1 WHERE email = ?", (email,))
    conn.commit()
