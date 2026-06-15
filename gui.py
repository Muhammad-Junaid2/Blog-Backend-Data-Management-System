"""
Tkinter GUI for Blog Backend System
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog

sys.path.insert(0, os.path.dirname(__file__))

from modules.database import init_db
from modules.users import (
    register_user, login_user, get_all_users,
    get_user_post_count, delete_user
)
from modules.posts import (
    create_post, get_all_posts, get_post_by_id,
    update_post, delete_post, react_to_post,
    get_categories, get_posts_by_author
)
from modules.comments import (
    add_comment, get_comments_for_post,
    delete_comment, get_comment_count
)
from modules.exporter import export_posts_to_pdf


# ─── Color palette ───────────────────────────────────────────────────────────
BG       = "#0f3460"
BG2      = "#16213e"
BG3      = "#1a1a2e"
ACCENT   = "#e94560"
ACCENT2  = "#0f3460"
FG       = "#eaeaea"
FG2      = "#a0aec0"
CARD     = "#1e3a5f"
CARD2    = "#162d4e"
SUCCESS  = "#48bb78"
WARNING  = "#ed8936"
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 14, "bold")
FONT_T   = ("Segoe UI", 18, "bold")


def styled_button(parent, text, command, bg=ACCENT, fg="white",
                  pad=(12, 6), font=FONT_B, **kwargs):
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, font=font,
        relief="flat", cursor="hand2",
        padx=pad[0], pady=pad[1],
        activebackground=ACCENT2, activeforeground="white",
        **kwargs
    )


def styled_entry(parent, width=30, show=None):
    e = tk.Entry(
        parent, bg=CARD2, fg=FG, insertbackground=FG,
        relief="flat", font=FONT, width=width,
        highlightthickness=1, highlightbackground="#2d5a8e",
        highlightcolor=ACCENT
    )
    if show:
        e.config(show=show)
    return e


def styled_label(parent, text, fg=FG, font=FONT, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"),
                    fg=fg, font=font, **kwargs)


# ─── App ─────────────────────────────────────────────────────────────────────

class BlogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_db()
        self.current_user = None
        self.current_page  = 1
        self.per_page      = 8
        self.search_kw     = tk.StringVar()
        self.filter_cat    = tk.StringVar(value="All")

        self.title("📝 Blog Backend System")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=BG3)

        self._build_ui()
        self.refresh_posts()

    # ── UI skeleton ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=BG3, pady=8)
        top.pack(fill="x", padx=0)
        styled_label(top, "📝 Blog Backend", fg=ACCENT, font=FONT_T).pack(side="left", padx=16)
        self.auth_frame = tk.Frame(top, bg=BG3)
        self.auth_frame.pack(side="right", padx=16)
        self._build_auth_bar()

        sep = tk.Frame(self, bg=ACCENT, height=2)
        sep.pack(fill="x")

        # Main area
        main = tk.Frame(self, bg=BG3)
        main.pack(fill="both", expand=True, padx=0)

        # Sidebar
        self.sidebar = tk.Frame(main, bg=BG2, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content
        self.content = tk.Frame(main, bg=BG3)
        self.content.pack(side="left", fill="both", expand=True)
        self._build_posts_panel()

    def _build_auth_bar(self):
        for w in self.auth_frame.winfo_children():
            w.destroy()
        if self.current_user:
            role_icon = "👑" if self.current_user["role"] == "admin" else "👤"
            styled_label(
                self.auth_frame,
                f"{role_icon} {self.current_user['username']}",
                fg=SUCCESS, font=FONT_B
            ).pack(side="left", padx=(0, 10))
            if self.current_user["role"] == "admin":
                styled_button(self.auth_frame, "Admin Panel",
                              self.open_admin, bg="#7b2d8b").pack(side="left", padx=4)
            styled_button(self.auth_frame, "Logout",
                          self.logout, bg=BG2).pack(side="left", padx=4)
        else:
            styled_button(self.auth_frame, "Login",
                          self.open_login).pack(side="left", padx=4)
            styled_button(self.auth_frame, "Register",
                          self.open_register, bg=BG2).pack(side="left", padx=4)

    def _build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()
        pad = {"padx": 12, "pady": 4, "fill": "x"}

        styled_label(self.sidebar, "MENU", fg=FG2, font=("Segoe UI", 9, "bold")).pack(pady=(18, 4), padx=12, anchor="w")

        buttons = [
            ("🏠  All Posts",      self.refresh_posts),
            ("✍️  New Post",       self.open_create_post),
            ("🔍  Search",         lambda: self.search_entry.focus()),
            ("📊  My Posts",       self.open_my_posts),
            ("📄  Export PDF",     self.export_pdf),
        ]
        for label, cmd in buttons:
            styled_button(self.sidebar, label, cmd, bg=BG2, fg=FG,
                          pad=(12, 8), anchor="w", width=18
                          ).pack(**pad)

        tk.Frame(self.sidebar, bg=BG2, height=1).pack(fill="x", padx=12, pady=8)
        styled_label(self.sidebar, "CATEGORIES", fg=FG2,
                     font=("Segoe UI", 9, "bold")).pack(padx=12, anchor="w")

        self.cat_buttons_frame = tk.Frame(self.sidebar, bg=BG2)
        self.cat_buttons_frame.pack(fill="x", padx=12, pady=4)
        self._refresh_category_list()

    def _refresh_category_list(self):
        for w in self.cat_buttons_frame.winfo_children():
            w.destroy()
        cats = ["All"] + get_categories()
        for cat in cats:
            c = cat
            btn = styled_button(
                self.cat_buttons_frame, cat,
                lambda x=c: self._filter_category(x),
                bg=BG3 if self.filter_cat.get() != cat else ACCENT,
                fg=FG, pad=(8, 4), anchor="w", width=18
            )
            btn.pack(fill="x", pady=1)

    def _build_posts_panel(self):
        for w in self.content.winfo_children():
            w.destroy()

        # Search bar
        search_bar = tk.Frame(self.content, bg=BG3, pady=8)
        search_bar.pack(fill="x", padx=16)
        styled_label(search_bar, "Search:", fg=FG2).pack(side="left")
        self.search_entry = styled_entry(search_bar, width=35)
        self.search_entry.pack(side="left", padx=(6, 4))
        if self.search_kw.get():
            self.search_entry.insert(0, self.search_kw.get())
        styled_button(search_bar, "🔍", self._do_search, pad=(8, 4)).pack(side="left")
        styled_button(search_bar, "✕ Clear",
                      self._clear_search, bg=BG2, pad=(8, 4)).pack(side="left", padx=4)

        self.search_entry.bind("<Return>", lambda e: self._do_search())

        # Status bar
        self.status_var = tk.StringVar(value="Loading…")
        styled_label(search_bar, "", textvariable=self.status_var,
                     fg=FG2).pack(side="right")

        # Scrollable posts
        canvas_frame = tk.Frame(self.content, bg=BG3)
        canvas_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self.canvas = tk.Canvas(canvas_frame, bg=BG3, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.posts_frame = tk.Frame(self.canvas, bg=BG3)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.posts_frame, anchor="nw"
        )
        self.posts_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # Pagination
        self.pagination_frame = tk.Frame(self.content, bg=BG3, pady=6)
        self.pagination_frame.pack(fill="x", padx=16)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    # ── Post list ─────────────────────────────────────────────────────────────

    def refresh_posts(self):
        self._build_posts_panel()
        cat = None if self.filter_cat.get() == "All" else self.filter_cat.get()
        kw  = self.search_kw.get() or None
        posts, total = get_all_posts(self.current_page, self.per_page, cat, kw)
        total_pages  = max(1, (total + self.per_page - 1) // self.per_page)

        self.status_var.set(
            f"Showing {len(posts)} of {total} posts  |  Page {self.current_page}/{total_pages}"
        )

        for p in posts:
            self._post_card(self.posts_frame, p)

        # Pagination buttons
        for w in self.pagination_frame.winfo_children():
            w.destroy()
        if self.current_page > 1:
            styled_button(self.pagination_frame, "◀ Prev",
                          self._prev_page, bg=BG2, pad=(10, 4)).pack(side="left")
        styled_label(self.pagination_frame,
                     f"Page {self.current_page} / {total_pages}",
                     fg=FG2).pack(side="left", padx=12)
        if self.current_page < total_pages:
            styled_button(self.pagination_frame, "Next ▶",
                          self._next_page, bg=BG2, pad=(10, 4)).pack(side="left")

        self._refresh_category_list()

    def _post_card(self, parent, p):
        card = tk.Frame(parent, bg=CARD, pady=10, padx=14, cursor="hand2")
        card.pack(fill="x", pady=5)

        # Title row
        title_row = tk.Frame(card, bg=CARD)
        title_row.pack(fill="x")
        styled_label(title_row, p["title"],
                     fg=FG, font=FONT_H).pack(side="left")
        cat_badge = tk.Label(title_row, text=f" {p['category']} ",
                             bg=ACCENT2, fg=ACCENT, font=("Segoe UI", 8, "bold"),
                             padx=6, pady=2)
        cat_badge.pack(side="right")

        # Meta
        cc = get_comment_count(p["id"])
        meta = (f"  ✍ {p['author']}   |   📅 {p['created_at'][:10]}"
                f"   |   👍 {p['likes']}  👎 {p['dislikes']}  💬 {cc}")
        styled_label(card, meta, fg=FG2, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 4))

        if p.get("tags"):
            styled_label(card, "🏷 " + p["tags"],
                         fg=ACCENT, font=("Segoe UI", 8)).pack(anchor="w")

        # Preview
        preview = p["content"][:160].replace("\n", " ")
        if len(p["content"]) > 160:
            preview += "…"
        styled_label(card, preview, fg=FG2,
                     font=("Segoe UI", 9), wraplength=780,
                     justify="left").pack(anchor="w", pady=(4, 6))

        # Action buttons
        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(anchor="w")
        pid = p["id"]
        styled_button(btn_row, "Read More",
                      lambda x=pid: self.open_post(x),
                      pad=(10, 3)).pack(side="left", padx=(0, 6))
        if self.current_user:
            if (self.current_user["role"] == "admin"
                    or self.current_user["id"] == p["author_id"]):
                styled_button(btn_row, "✏ Edit",
                              lambda x=pid: self.open_edit_post(x),
                              bg=WARNING, pad=(10, 3)).pack(side="left", padx=3)
                styled_button(btn_row, "🗑 Delete",
                              lambda x=pid, t=p["title"]: self._delete_post(x, t),
                              bg="#c0392b", pad=(10, 3)).pack(side="left", padx=3)

    # ── Post detail ───────────────────────────────────────────────────────────

    def open_post(self, post_id: int):
        post = get_post_by_id(post_id)
        if not post:
            messagebox.showerror("Error", "Post not found.")
            return

        win = tk.Toplevel(self)
        win.title(post["title"])
        win.geometry("760x600")
        win.configure(bg=BG3)

        frame = tk.Frame(win, bg=BG3)
        frame.pack(fill="both", expand=True, padx=20, pady=12)

        styled_label(frame, post["title"], fg=FG, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        cc = get_comment_count(post_id)
        styled_label(
            frame,
            f"By {post['author']}  |  {post['category']}"
            f"  |  👍 {post['likes']}  👎 {post['dislikes']}  💬 {cc}"
            f"  |  {post['created_at'][:16]}",
            fg=FG2, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(2, 6))

        tk.Frame(frame, bg=ACCENT, height=1).pack(fill="x", pady=4)

        txt = scrolledtext.ScrolledText(frame, bg=CARD, fg=FG, font=FONT,
                                        relief="flat", wrap="word", height=10)
        txt.insert("1.0", post["content"])
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=False, pady=6)

        # Reactions
        react_row = tk.Frame(frame, bg=BG3)
        react_row.pack(anchor="w", pady=4)
        if self.current_user:
            styled_button(react_row, f"👍 Like ({post['likes']})",
                          lambda: self._react(post_id, "like", win),
                          bg=SUCCESS, pad=(10, 4)).pack(side="left", padx=(0, 6))
            styled_button(react_row, f"👎 Dislike ({post['dislikes']})",
                          lambda: self._react(post_id, "dislike", win),
                          bg="#c0392b", pad=(10, 4)).pack(side="left")

        # Comments
        tk.Frame(frame, bg=ACCENT, height=1).pack(fill="x", pady=8)
        styled_label(frame, "💬 Comments", fg=FG, font=FONT_H).pack(anchor="w")

        comments = get_comments_for_post(post_id)
        c_frame = tk.Frame(frame, bg=BG3)
        c_frame.pack(fill="x")
        for c in comments:
            cf = tk.Frame(c_frame, bg=CARD2, pady=6, padx=10)
            cf.pack(fill="x", pady=2)
            styled_label(cf, f"🗨 {c['commenter']}  —  {c['created_at'][:16]}",
                         fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            styled_label(cf, c["message"], fg=FG,
                         font=("Segoe UI", 9), wraplength=680,
                         justify="left").pack(anchor="w")
            if self.current_user and self.current_user["role"] == "admin":
                styled_button(cf, "✕",
                              lambda cid=c["id"]: self._delete_comment(cid, win, post_id),
                              bg="#c0392b", pad=(4, 2),
                              font=("Segoe UI", 8)).pack(anchor="e")

        # Add comment
        tk.Frame(frame, bg=BG2, height=1).pack(fill="x", pady=6)
        styled_label(frame, "Add a Comment", fg=FG, font=FONT_B).pack(anchor="w")

        name_var = tk.StringVar(
            value=self.current_user["username"] if self.current_user else ""
        )
        name_e = styled_entry(frame, width=30)
        if self.current_user:
            name_e.insert(0, self.current_user["username"])
            name_e.configure(state="disabled")
        else:
            styled_label(frame, "Your name:").pack(anchor="w")
        name_e.pack(anchor="w", pady=2)

        msg_e = scrolledtext.ScrolledText(frame, bg=CARD2, fg=FG,
                                          insertbackground=FG, relief="flat",
                                          font=FONT, height=3, wrap="word")
        msg_e.pack(fill="x", pady=4)

        def submit_comment():
            name = (self.current_user["username"] if self.current_user
                    else name_e.get().strip())
            msg = msg_e.get("1.0", "end").strip()
            try:
                add_comment(post_id, name, msg)
                messagebox.showinfo("✅", "Comment added!", parent=win)
                win.destroy()
                self.open_post(post_id)
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=win)

        styled_button(frame, "Submit Comment", submit_comment,
                      pad=(14, 6)).pack(anchor="w", pady=4)

    def _react(self, post_id, reaction, win):
        if not self.current_user:
            messagebox.showinfo("Login required", "Please log in to react.")
            return
        try:
            react_to_post(post_id, self.current_user["id"], reaction)
            win.destroy()
            self.open_post(post_id)
            self.refresh_posts()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_comment(self, comment_id, win, post_id):
        if messagebox.askyesno("Confirm", "Delete this comment?", parent=win):
            delete_comment(comment_id)
            win.destroy()
            self.open_post(post_id)

    # ── Create / Edit post ────────────────────────────────────────────────────

    def open_create_post(self):
        if not self.current_user:
            messagebox.showinfo("Login required", "Please log in to create a post.")
            return
        self._post_form()

    def open_edit_post(self, post_id: int):
        post = get_post_by_id(post_id)
        if not post:
            messagebox.showerror("Error", "Post not found.")
            return
        if (self.current_user["role"] != "admin"
                and self.current_user["id"] != post["author_id"]):
            messagebox.showerror("Error", "You can only edit your own posts.")
            return
        self._post_form(post)

    def _post_form(self, post=None):
        win = tk.Toplevel(self)
        win.title("Edit Post" if post else "Create Post")
        win.geometry("680x560")
        win.configure(bg=BG3)

        frame = tk.Frame(win, bg=BG3, padx=24, pady=16)
        frame.pack(fill="both", expand=True)

        styled_label(frame, "Edit Post" if post else "New Post",
                     fg=FG, font=FONT_T).pack(anchor="w", pady=(0, 10))

        def row(label):
            styled_label(frame, label, fg=FG2, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 1))

        row("Title *")
        title_e = styled_entry(frame, width=60)
        title_e.pack(anchor="w")
        if post:
            title_e.insert(0, post["title"])

        row2 = tk.Frame(frame, bg=BG3)
        row2.pack(fill="x", pady=(8, 0))
        cat_frame = tk.Frame(row2, bg=BG3)
        cat_frame.pack(side="left", padx=(0, 20))
        styled_label(cat_frame, "Category", fg=FG2, font=("Segoe UI", 9)).pack(anchor="w")
        cat_e = styled_entry(cat_frame, width=20)
        cat_e.pack()
        if post:
            cat_e.insert(0, post["category"])
        else:
            cat_e.insert(0, "General")

        tags_frame = tk.Frame(row2, bg=BG3)
        tags_frame.pack(side="left")
        styled_label(tags_frame, "Tags (comma-separated)", fg=FG2,
                     font=("Segoe UI", 9)).pack(anchor="w")
        tags_e = styled_entry(tags_frame, width=30)
        tags_e.pack()
        if post:
            tags_e.insert(0, post.get("tags", ""))

        row("Content *")
        content_e = scrolledtext.ScrolledText(
            frame, bg=CARD2, fg=FG, insertbackground=FG,
            relief="flat", font=FONT, height=12, wrap="word"
        )
        content_e.pack(fill="both", expand=True, pady=4)
        if post:
            content_e.insert("1.0", post["content"])

        def save():
            title   = title_e.get().strip()
            cat     = cat_e.get().strip() or "General"
            tags    = tags_e.get().strip()
            content = content_e.get("1.0", "end").strip()
            try:
                if post:
                    update_post(post["id"], title, content, cat, tags)
                    messagebox.showinfo("✅", "Post updated!", parent=win)
                else:
                    create_post(title, content, self.current_user["id"], cat, tags)
                    messagebox.showinfo("✅", "Post created!", parent=win)
                win.destroy()
                self.refresh_posts()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=win)

        styled_button(frame, "💾 Save Post", save, pad=(16, 8)).pack(anchor="e", pady=8)

    def _delete_post(self, post_id: int, title: str):
        if messagebox.askyesno("Confirm Delete",
                               f"Delete post:\n'{title}'?\n\nThis cannot be undone."):
            try:
                delete_post(post_id)
                self.refresh_posts()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    # ── My posts ──────────────────────────────────────────────────────────────

    def open_my_posts(self):
        if not self.current_user:
            messagebox.showinfo("Login required", "Please log in to view your posts.")
            return
        win = tk.Toplevel(self)
        win.title("My Posts")
        win.geometry("700x480")
        win.configure(bg=BG3)
        frame = tk.Frame(win, bg=BG3, padx=20, pady=14)
        frame.pack(fill="both", expand=True)

        styled_label(frame, f"📚 My Posts — {self.current_user['username']}",
                     fg=FG, font=FONT_H).pack(anchor="w", pady=(0, 10))

        posts = get_posts_by_author(self.current_user["id"])
        if not posts:
            styled_label(frame, "You haven't written any posts yet.", fg=FG2).pack()
            return

        cols = ("ID", "Title", "Category", "👍", "👎", "💬", "Date")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col, w in zip(cols, (40, 320, 100, 40, 40, 40, 100)):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center" if col != "Title" else "w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=CARD, foreground=FG,
                        fieldbackground=CARD, rowheight=24, font=FONT)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT,
                        font=FONT_B)
        style.map("Treeview", background=[("selected", ACCENT)])

        for p in posts:
            cc = get_comment_count(p["id"])
            tree.insert("", "end", iid=str(p["id"]),
                        values=(p["id"], p["title"], p["category"],
                                p["likes"], p["dislikes"], cc,
                                p["created_at"][:10]))
        tree.pack(fill="both", expand=True)

        def on_double(event):
            sel = tree.selection()
            if sel:
                self.open_post(int(sel[0]))
        tree.bind("<Double-1>", on_double)

    # ── Auth ──────────────────────────────────────────────────────────────────

    def open_login(self):
        win = tk.Toplevel(self)
        win.title("Login")
        win.geometry("360x260")
        win.configure(bg=BG3)
        win.resizable(False, False)
        f = tk.Frame(win, bg=BG3, padx=30, pady=20)
        f.pack(fill="both", expand=True)

        styled_label(f, "Login", fg=FG, font=FONT_T).pack(pady=(0, 12))
        styled_label(f, "Username", fg=FG2).pack(anchor="w")
        user_e = styled_entry(f, width=32)
        user_e.pack(anchor="w", pady=(0, 8))
        styled_label(f, "Password", fg=FG2).pack(anchor="w")
        pass_e = styled_entry(f, width=32, show="•")
        pass_e.pack(anchor="w", pady=(0, 12))

        def do_login():
            try:
                self.current_user = login_user(user_e.get(), pass_e.get())
                self._build_auth_bar()
                self._build_sidebar()
                win.destroy()
                messagebox.showinfo("✅", f"Welcome back, {self.current_user['username']}!")
                self.refresh_posts()
            except ValueError as e:
                messagebox.showerror("Login Failed", str(e), parent=win)

        pass_e.bind("<Return>", lambda e: do_login())
        styled_button(f, "Login", do_login, pad=(14, 8)).pack()

    def open_register(self):
        win = tk.Toplevel(self)
        win.title("Register")
        win.geometry("360x320")
        win.configure(bg=BG3)
        win.resizable(False, False)
        f = tk.Frame(win, bg=BG3, padx=30, pady=20)
        f.pack(fill="both", expand=True)

        styled_label(f, "Register", fg=FG, font=FONT_T).pack(pady=(0, 12))

        fields = {}
        for label, show in [("Username", None), ("Email", None),
                             ("Password", "•"), ("Confirm Password", "•")]:
            styled_label(f, label, fg=FG2).pack(anchor="w")
            e = styled_entry(f, width=32, show=show)
            e.pack(anchor="w", pady=(0, 6))
            fields[label] = e

        def do_register():
            pw = fields["Password"].get()
            if pw != fields["Confirm Password"].get():
                messagebox.showerror("Error", "Passwords do not match.", parent=win)
                return
            try:
                self.current_user = register_user(
                    fields["Username"].get(),
                    fields["Email"].get(),
                    pw
                )
                self._build_auth_bar()
                self._build_sidebar()
                win.destroy()
                messagebox.showinfo("✅", f"Welcome, {self.current_user['username']}!")
                self.refresh_posts()
            except ValueError as e:
                messagebox.showerror("Registration Failed", str(e), parent=win)

        styled_button(f, "Create Account", do_register, pad=(14, 8)).pack(pady=4)

    def logout(self):
        self.current_user = None
        self._build_auth_bar()
        self._build_sidebar()
        self.refresh_posts()

    # ── Admin panel ───────────────────────────────────────────────────────────

    def open_admin(self):
        if not self.current_user or self.current_user["role"] != "admin":
            return
        win = tk.Toplevel(self)
        win.title("Admin Panel")
        win.geometry("780x500")
        win.configure(bg=BG3)

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # Users tab
        u_frame = tk.Frame(nb, bg=BG3)
        nb.add(u_frame, text="👥 Users")

        cols = ("ID", "Username", "Email", "Role", "Posts", "Joined")
        tree = ttk.Treeview(u_frame, columns=cols, show="headings", height=16)
        for col, w in zip(cols, (40, 140, 240, 60, 50, 110)):
            tree.heading(col, text=col)
            tree.column(col, width=w)

        style = ttk.Style()
        style.configure("Treeview", background=CARD, foreground=FG,
                        fieldbackground=CARD, rowheight=24, font=FONT)
        style.configure("Treeview.Heading", background=BG2,
                        foreground=ACCENT, font=FONT_B)

        for u in get_all_users():
            pc = get_user_post_count(u["id"])
            tree.insert("", "end", iid=str(u["id"]),
                        values=(u["id"], u["username"], u["email"],
                                u["role"], pc, u["created_at"][:10]))
        tree.pack(fill="both", expand=True)

        def del_user():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select a user first.", parent=win)
                return
            uid = int(sel[0])
            if uid == self.current_user["id"]:
                messagebox.showwarning("Warning", "Cannot delete yourself.", parent=win)
                return
            if messagebox.askyesno("Confirm", "Delete this user and all their posts?", parent=win):
                delete_user(uid)
                tree.delete(sel[0])

        styled_button(u_frame, "🗑 Delete Selected User",
                      del_user, bg="#c0392b", pad=(10, 5)).pack(pady=6)

        # Posts tab
        p_frame = tk.Frame(nb, bg=BG3)
        nb.add(p_frame, text="📝 All Posts")

        pcols = ("ID", "Title", "Author", "Category", "👍", "👎", "Date")
        ptree = ttk.Treeview(p_frame, columns=pcols, show="headings", height=16)
        for col, w in zip(pcols, (40, 260, 100, 90, 40, 40, 100)):
            ptree.heading(col, text=col)
            ptree.column(col, width=w)

        posts, _ = get_all_posts(per_page=200)
        for p in posts:
            ptree.insert("", "end", iid=str(p["id"]),
                         values=(p["id"], p["title"], p["author"],
                                 p["category"], p["likes"], p["dislikes"],
                                 p["created_at"][:10]))
        ptree.pack(fill="both", expand=True)

        def del_post():
            sel = ptree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select a post first.", parent=win)
                return
            if messagebox.askyesno("Confirm", "Delete this post?", parent=win):
                try:
                    delete_post(int(sel[0]))
                    ptree.delete(sel[0])
                    self.refresh_posts()
                except Exception as e:
                    messagebox.showerror("Error", str(e), parent=win)

        styled_button(p_frame, "🗑 Delete Selected Post",
                      del_post, bg="#c0392b", pad=(10, 5)).pack(pady=6)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _do_search(self):
        self.search_kw.set(self.search_entry.get().strip())
        self.current_page = 1
        self.refresh_posts()

    def _clear_search(self):
        self.search_kw.set("")
        self.current_page = 1
        self.refresh_posts()

    def _filter_category(self, cat: str):
        self.filter_cat.set(cat)
        self.current_page = 1
        self.refresh_posts()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_posts()

    def _next_page(self):
        self.current_page += 1
        self.refresh_posts()

    def export_pdf(self):
        posts, total = get_all_posts(per_page=1000)
        if not posts:
            messagebox.showinfo("Export", "No posts to export.")
            return
        try:
            path = export_posts_to_pdf(posts)
            messagebox.showinfo("✅ Export Complete",
                                f"Exported {len(posts)} posts to:\n{path}")
        except RuntimeError as e:
            messagebox.showerror("Export Failed", str(e))


def main():
    init_db()
    app = BlogApp()
    app.mainloop()


if __name__ == "__main__":
    main()
