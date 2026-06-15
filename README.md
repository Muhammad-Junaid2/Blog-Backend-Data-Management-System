# 📝 Blog Backend System

A full-featured Python blog backend with both **CLI** and **Tkinter GUI** interfaces, powered by **SQLite**.

---

## ✨ Features

### Blog Posts
- Create, Read, Update, Delete (CRUD)
- Category & tag support
- Like / Dislike reactions (per-user, toggleable)
- Search by keyword (title, content, tags)
- Category filtering
- Pagination (8 posts/page in GUI, 5 in CLI)

### User Management
- Register & Login
- Password hashing (SHA-256 + salt)
- Role system: `user` / `admin`
- View personal post history

### Comment System
- Add comments on any post
- View all comments under a post
- Admin can delete any comment

### Admin Panel (GUI)
- View & delete all users
- View & delete all posts

### Export
- Export all posts to a formatted PDF (via ReportLab)

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install reportlab
```
> `tkinter` and `sqlite3` are bundled with Python — no extra install needed.

### 2. Seed sample data
```bash
python main.py --seed
```
This creates sample users, posts, and comments.

**Demo credentials:**
| Username | Password   | Role  |
|----------|------------|-------|
| admin    | Admin@123  | admin |
| alice    | Alice@123  | user  |
| bob      | Bob@123    | user  |
| charlie  | Charlie@123| user  |

### 3. Launch GUI (default)
```bash
python main.py
```

### 4. Launch CLI
```bash
python main.py --cli
```

---

## 📁 Project Structure

```
blog_system/
├── main.py              # Entry point (GUI / CLI / seed)
├── gui.py               # Tkinter GUI application
├── cli.py               # CLI application
├── seed.py              # Sample data seeder
├── blog.db              # SQLite database (auto-created)
├── exports/             # PDF exports saved here
├── modules/
│   ├── database.py      # Schema & connection management
│   ├── users.py         # User registration, login, profiles
│   ├── posts.py         # Post CRUD, search, reactions
│   ├── comments.py      # Comment management
│   └── exporter.py      # PDF export via ReportLab
└── README.md
```

---

## 🗄️ Database Schema

**users** — id, username, email, password (hashed), role, created_at  
**posts** — id, title, content, author_id, category, tags, likes, dislikes, created_at, updated_at  
**comments** — id, post_id, commenter, message, created_at  
**post_reactions** — id, post_id, user_id, reaction (UNIQUE per user/post)

---

## 🔒 Security

- Passwords stored as `salt:sha256(salt+password)` — never plain text
- Foreign key constraints enforce data integrity
- Parameterized SQL queries prevent SQL injection
- Input validation on all user-facing fields

---

## 📦 Requirements

- Python 3.8+
- `reportlab` (for PDF export only)
- `tkinter` (bundled with Python)
- `sqlite3` (bundled with Python)
