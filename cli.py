"""
CLI interface for Blog Backend System
"""
import os
import sys

# ─── Add project root to path ─────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from modules.database import init_db
from modules.users import (
    register_user, login_user, get_all_users,
    get_user_post_count, delete_user
)
from modules.posts import (
    create_post, get_all_posts, get_post_by_id,
    update_post, delete_post, react_to_post,
    get_categories
)
from modules.comments import add_comment, get_comments_for_post, delete_comment
from modules.exporter import export_posts_to_pdf


# ─── Helpers ──────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\n  Press Enter to continue...")


def separator(char="─", width=60):
    print(char * width)


def header(title: str):
    clear()
    separator("═")
    print(f"  📝  BLOG BACKEND SYSTEM  |  {title}")
    separator("═")
    print()


def prompt(label: str, required: bool = True) -> str:
    while True:
        val = input(f"  {label}: ").strip()
        if val or not required:
            return val
        print("  ⚠️  This field is required.")


def multiline_prompt(label: str) -> str:
    print(f"  {label} (type END on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


# ─── State ────────────────────────────────────────────────────────────────────

current_user = None   # dict or None


# ─── Auth screens ─────────────────────────────────────────────────────────────

def screen_register():
    global current_user
    header("Register")
    username = prompt("Username")
    email    = prompt("Email")
    password = prompt("Password (min 6 chars)")
    try:
        current_user = register_user(username, email, password)
        print(f"\n  ✅ Welcome, {current_user['username']}! Account created.")
    except ValueError as e:
        print(f"\n  ❌ {e}")
    pause()


def screen_login():
    global current_user
    header("Login")
    username = prompt("Username")
    password = prompt("Password")
    try:
        current_user = login_user(username, password)
        print(f"\n  ✅ Welcome back, {current_user['username']}!")
    except ValueError as e:
        print(f"\n  ❌ {e}")
    pause()


def screen_logout():
    global current_user
    print(f"\n  👋 Goodbye, {current_user['username']}!")
    current_user = None
    pause()


# ─── Post screens ─────────────────────────────────────────────────────────────

def screen_view_posts():
    page = 1
    per_page = 5
    keyword = None
    category = None

    while True:
        header("View Posts")
        posts, total = get_all_posts(page, per_page, category, keyword)
        total_pages = max(1, (total + per_page - 1) // per_page)

        filters = []
        if keyword:
            filters.append(f"keyword='{keyword}'")
        if category:
            filters.append(f"category='{category}'")
        print(f"  Total: {total} posts  |  Page {page}/{total_pages}"
              + (f"  |  Filters: {', '.join(filters)}" if filters else ""))
        separator()

        if not posts:
            print("  No posts found.")
        else:
            for p in posts:
                from modules.comments import get_comment_count
                cc = get_comment_count(p["id"])
                print(f"  [{p['id']:>3}] {p['title'][:48]}")
                print(f"        by {p['author']}  |  {p['category']}  |"
                      f"  👍{p['likes']} 👎{p['dislikes']}  💬{cc}"
                      f"  |  {p['created_at'][:10]}")
                if p.get("tags"):
                    print(f"        🏷  {p['tags']}")
                print()

        separator()
        print("  [n] Next  [p] Prev  [s] Search  [f] Filter category"
              "  [r] Read post  [c] Clear filters  [q] Back")
        choice = input("\n  > ").strip().lower()

        if choice == "n" and page < total_pages:
            page += 1
        elif choice == "p" and page > 1:
            page -= 1
        elif choice == "s":
            keyword = prompt("Search keyword", required=False) or None
            page = 1
        elif choice == "f":
            cats = get_categories()
            if cats:
                print("  Categories: " + ", ".join(cats))
            category = prompt("Category", required=False) or None
            page = 1
        elif choice == "c":
            keyword = None
            category = None
            page = 1
        elif choice == "r":
            pid = input("  Post ID: ").strip()
            if pid.isdigit():
                screen_read_post(int(pid))
        elif choice == "q":
            break


def screen_read_post(post_id: int):
    header("Read Post")
    post = get_post_by_id(post_id)
    if not post:
        print(f"  ❌ Post {post_id} not found.")
        pause()
        return

    print(f"  {post['title']}")
    separator()
    print(f"  By {post['author']}  |  {post['category']}"
          f"  |  👍 {post['likes']}  👎 {post['dislikes']}")
    print(f"  Tags: {post['tags'] or 'None'}")
    print(f"  Created: {post['created_at'][:16]}  |  Updated: {post['updated_at'][:16]}")
    separator()
    print()
    for line in post["content"].split("\n"):
        print(f"  {line}")
    print()

    comments = get_comments_for_post(post_id)
    separator()
    print(f"  💬 Comments ({len(comments)})")
    separator()
    if comments:
        for c in comments:
            print(f"  [{c['id']}] {c['commenter']} — {c['created_at'][:16]}")
            print(f"      {c['message']}")
            print()
    else:
        print("  No comments yet.")

    separator()
    opts = "[c] Add comment  [q] Back"
    if current_user:
        opts = "[l] Like  [d] Dislike  [c] Add comment  [q] Back"
        if current_user["role"] == "admin" or current_user["id"] == post["author_id"]:
            opts += "  [e] Edit  [x] Delete"
    print(f"  {opts}")
    choice = input("\n  > ").strip().lower()

    if choice == "l" and current_user:
        try:
            react_to_post(post_id, current_user["id"], "like")
            print("  👍 Liked!")
        except Exception as e:
            print(f"  ❌ {e}")
        pause()
    elif choice == "d" and current_user:
        try:
            react_to_post(post_id, current_user["id"], "dislike")
            print("  👎 Disliked!")
        except Exception as e:
            print(f"  ❌ {e}")
        pause()
    elif choice == "c":
        name = current_user["username"] if current_user else prompt("Your name")
        msg = prompt("Comment")
        try:
            add_comment(post_id, name, msg)
            print("  ✅ Comment added!")
        except ValueError as e:
            print(f"  ❌ {e}")
        pause()
    elif choice == "e" and current_user:
        screen_edit_post(post_id)
    elif choice == "x" and current_user:
        confirm = input(f"  Delete post '{post['title']}'? [y/N]: ").strip().lower()
        if confirm == "y":
            delete_post(post_id)
            print("  ✅ Post deleted.")
            pause()
            return


def screen_create_post():
    header("Create Post")
    if not current_user:
        print("  ❌ You must be logged in to create a post.")
        pause()
        return

    title    = prompt("Title")
    category = prompt("Category (e.g. Python, Web, General)", required=False) or "General"
    tags     = prompt("Tags (comma-separated)", required=False)
    content  = multiline_prompt("Content")

    try:
        post = create_post(title, content, current_user["id"], category, tags)
        print(f"\n  ✅ Post created! ID: {post['id']}")
    except ValueError as e:
        print(f"\n  ❌ {e}")
    pause()


def screen_edit_post(post_id: int = None):
    header("Edit Post")
    if not current_user:
        print("  ❌ You must be logged in to edit posts.")
        pause()
        return

    if post_id is None:
        pid = input("  Post ID to edit: ").strip()
        if not pid.isdigit():
            print("  ❌ Invalid ID.")
            pause()
            return
        post_id = int(pid)

    post = get_post_by_id(post_id)
    if not post:
        print(f"  ❌ Post {post_id} not found.")
        pause()
        return
    if current_user["role"] != "admin" and current_user["id"] != post["author_id"]:
        print("  ❌ You can only edit your own posts.")
        pause()
        return

    print(f"  Editing: {post['title']} (leave blank to keep current)")
    separator()

    title    = input(f"  Title [{post['title']}]: ").strip() or None
    category = input(f"  Category [{post['category']}]: ").strip() or None
    tags     = input(f"  Tags [{post['tags']}]: ").strip() or None
    print(f"  Current content (first 100 chars): {post['content'][:100]}...")
    edit_content = input("  Edit content? [y/N]: ").strip().lower()
    content = None
    if edit_content == "y":
        content = multiline_prompt("New content")

    try:
        updated = update_post(post_id, title, content, category, tags)
        print(f"\n  ✅ Post updated: {updated['title']}")
    except ValueError as e:
        print(f"\n  ❌ {e}")
    pause()


def screen_delete_post():
    header("Delete Post")
    if not current_user:
        print("  ❌ You must be logged in.")
        pause()
        return
    pid = input("  Post ID to delete: ").strip()
    if not pid.isdigit():
        print("  ❌ Invalid ID.")
        pause()
        return
    post = get_post_by_id(int(pid))
    if not post:
        print("  ❌ Post not found.")
        pause()
        return
    if current_user["role"] != "admin" and current_user["id"] != post["author_id"]:
        print("  ❌ You can only delete your own posts.")
        pause()
        return
    confirm = input(f"  Delete '{post['title']}'? [y/N]: ").strip().lower()
    if confirm == "y":
        delete_post(int(pid))
        print("  ✅ Post deleted.")
    pause()


def screen_export():
    header("Export Posts to PDF")
    posts, total = get_all_posts(per_page=1000)
    if not posts:
        print("  No posts to export.")
        pause()
        return
    print(f"  {total} posts found.")
    choice = input("  Export all? [y/N]: ").strip().lower()
    if choice == "y":
        try:
            path = export_posts_to_pdf(posts)
            print(f"\n  ✅ Exported to: {path}")
        except RuntimeError as e:
            print(f"\n  ❌ {e}")
    pause()


# ─── Admin screens ────────────────────────────────────────────────────────────

def screen_admin():
    while True:
        header("Admin Panel")
        if not current_user or current_user["role"] != "admin":
            print("  ❌ Admin access required.")
            pause()
            return

        print("  [1] List all users")
        print("  [2] Delete user")
        print("  [3] Delete any post")
        print("  [4] Delete comment")
        print("  [q] Back")
        choice = input("\n  > ").strip().lower()

        if choice == "1":
            header("All Users")
            for u in get_all_users():
                pc = get_user_post_count(u["id"])
                print(f"  [{u['id']:>3}] {u['username']:<15} {u['email']:<30}"
                      f" {u['role']:<6}  Posts: {pc}")
            pause()
        elif choice == "2":
            uid = input("  User ID to delete: ").strip()
            if uid.isdigit():
                delete_user(int(uid))
                print("  ✅ User deleted.")
            pause()
        elif choice == "3":
            pid = input("  Post ID to delete: ").strip()
            if pid.isdigit():
                try:
                    delete_post(int(pid))
                    print("  ✅ Post deleted.")
                except ValueError as e:
                    print(f"  ❌ {e}")
            pause()
        elif choice == "4":
            cid = input("  Comment ID to delete: ").strip()
            if cid.isdigit():
                delete_comment(int(cid))
                print("  ✅ Comment deleted.")
            pause()
        elif choice == "q":
            break


# ─── Main menu ────────────────────────────────────────────────────────────────

def main_menu():
    while True:
        header("Main Menu")
        user_info = (f"👤 {current_user['username']} ({current_user['role']})"
                     if current_user else "👤 Not logged in")
        print(f"  {user_info}")
        separator()
        print("  [1] View Posts")
        print("  [2] Create Post")
        print("  [3] Edit Post")
        print("  [4] Delete Post")
        print("  [5] Export Posts to PDF")
        separator("─")
        if current_user:
            print("  [6] Logout")
            if current_user["role"] == "admin":
                print("  [7] Admin Panel")
        else:
            print("  [6] Login")
            print("  [7] Register")
        print("  [q] Exit")
        separator()

        choice = input("  Choice: ").strip().lower()

        if choice == "1":
            screen_view_posts()
        elif choice == "2":
            screen_create_post()
        elif choice == "3":
            screen_edit_post()
        elif choice == "4":
            screen_delete_post()
        elif choice == "5":
            screen_export()
        elif choice == "6":
            if current_user:
                screen_logout()
            else:
                screen_login()
        elif choice == "7":
            if current_user and current_user["role"] == "admin":
                screen_admin()
            else:
                screen_register()
        elif choice == "q":
            print("\n  👋 Goodbye!\n")
            sys.exit(0)


def main():
    init_db()
    main_menu()


if __name__ == "__main__":
    main()
