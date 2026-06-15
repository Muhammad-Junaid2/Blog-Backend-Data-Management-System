"""
Blog post management - CRUD, search, filtering, pagination, reactions
"""
from modules.database import get_connection


def create_post(title: str, content: str, author_id: int,
                category: str = "General", tags: str = ""):
    if not title.strip():
        raise ValueError("Title cannot be empty.")
    if not content.strip():
        raise ValueError("Content cannot be empty.")

    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO posts (title, content, author_id, category, tags)
           VALUES (?,?,?,?,?)""",
        (title.strip(), content.strip(), author_id,
         category.strip() or "General", tags.strip()),
    )
    post_id = cur.lastrowid
    conn.commit()
    conn.close()
    return get_post_by_id(post_id)


def get_post_by_id(post_id: int):
    conn = get_connection()
    row = conn.execute(
        """SELECT p.*, u.username AS author
           FROM posts p JOIN users u ON p.author_id = u.id
           WHERE p.id=?""",
        (post_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_posts(page: int = 1, per_page: int = 10,
                  category: str = None, keyword: str = None):
    conn = get_connection()
    conditions = []
    params = []

    if category:
        conditions.append("LOWER(p.category) = LOWER(?)")
        params.append(category)
    if keyword:
        conditions.append("(LOWER(p.title) LIKE ? OR LOWER(p.content) LIKE ? OR LOWER(p.tags) LIKE ?)")
        kw = f"%{keyword.lower()}%"
        params.extend([kw, kw, kw])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    total = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM posts p {where}", params
    ).fetchone()["cnt"]

    offset = (page - 1) * per_page
    rows = conn.execute(
        f"""SELECT p.*, u.username AS author
            FROM posts p JOIN users u ON p.author_id = u.id
            {where}
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?""",
        params + [per_page, offset],
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows], total


def update_post(post_id: int, title: str = None, content: str = None,
                category: str = None, tags: str = None):
    post = get_post_by_id(post_id)
    if not post:
        raise ValueError(f"Post ID {post_id} not found.")

    new_title   = title.strip()   if title   is not None else post["title"]
    new_content = content.strip() if content is not None else post["content"]
    new_cat     = category.strip() if category is not None else post["category"]
    new_tags    = tags.strip()    if tags    is not None else post["tags"]

    if not new_title:
        raise ValueError("Title cannot be empty.")
    if not new_content:
        raise ValueError("Content cannot be empty.")

    conn = get_connection()
    conn.execute(
        """UPDATE posts SET title=?, content=?, category=?, tags=?,
                            updated_at=datetime('now')
           WHERE id=?""",
        (new_title, new_content, new_cat, new_tags, post_id),
    )
    conn.commit()
    conn.close()
    return get_post_by_id(post_id)


def delete_post(post_id: int):
    if not get_post_by_id(post_id):
        raise ValueError(f"Post ID {post_id} not found.")
    conn = get_connection()
    conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()


def react_to_post(post_id: int, user_id: int, reaction: str):
    """reaction: 'like' or 'dislike'. Toggles off if same reaction sent again."""
    if reaction not in ("like", "dislike"):
        raise ValueError("Reaction must be 'like' or 'dislike'.")
    if not get_post_by_id(post_id):
        raise ValueError(f"Post ID {post_id} not found.")

    conn = get_connection()
    existing = conn.execute(
        "SELECT reaction FROM post_reactions WHERE post_id=? AND user_id=?",
        (post_id, user_id),
    ).fetchone()

    if existing:
        if existing["reaction"] == reaction:
            # toggle off
            conn.execute(
                "DELETE FROM post_reactions WHERE post_id=? AND user_id=?",
                (post_id, user_id),
            )
            delta = -1
            col = reaction + "s"
            conn.execute(f"UPDATE posts SET {col}=MAX(0,{col}-1) WHERE id=?", (post_id,))
        else:
            # switch reaction
            old_col = existing["reaction"] + "s"
            new_col = reaction + "s"
            conn.execute(
                "UPDATE post_reactions SET reaction=? WHERE post_id=? AND user_id=?",
                (reaction, post_id, user_id),
            )
            conn.execute(
                f"UPDATE posts SET {old_col}=MAX(0,{old_col}-1), {new_col}={new_col}+1 WHERE id=?",
                (post_id,),
            )
    else:
        conn.execute(
            "INSERT INTO post_reactions (post_id, user_id, reaction) VALUES (?,?,?)",
            (post_id, user_id, reaction),
        )
        col = reaction + "s"
        conn.execute(f"UPDATE posts SET {col}={col}+1 WHERE id=?", (post_id,))

    conn.commit()
    conn.close()
    return get_post_by_id(post_id)


def get_categories():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM posts ORDER BY category"
    ).fetchall()
    conn.close()
    return [r["category"] for r in rows]


def get_posts_by_author(author_id: int):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username AS author
           FROM posts p JOIN users u ON p.author_id = u.id
           WHERE p.author_id=?
           ORDER BY p.created_at DESC""",
        (author_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
