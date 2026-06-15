"""
User management - register, login, profiles, password hashing
"""
import hashlib
import secrets
from modules.database import get_connection


def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except Exception:
        return False


def register_user(username: str, email: str, password: str, role: str = "user"):
    if not username.strip() or not email.strip() or not password.strip():
        raise ValueError("Username, email, and password are required.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    if "@" not in email:
        raise ValueError("Invalid email address.")

    pw_hash = _hash_password(password)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?,?,?,?)",
            (username.strip(), email.strip().lower(), pw_hash, role),
        )
        conn.commit()
        return get_user_by_username(username.strip())
    except Exception as e:
        if "UNIQUE" in str(e):
            raise ValueError("Username or email already exists.")
        raise
    finally:
        conn.close()


def login_user(username: str, password: str):
    if not username.strip() or not password.strip():
        raise ValueError("Username and password are required.")
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=?", (username.strip(),)
    ).fetchone()
    conn.close()
    if row is None or not _verify_password(password, row["password"]):
        raise ValueError("Invalid username or password.")
    return dict(row)


def get_user_by_id(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, email, role, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def get_user_post_count(user_id: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM posts WHERE author_id=?", (user_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0
