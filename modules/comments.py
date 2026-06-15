"""
Comment management - add, view, delete comments
"""
from modules.database import get_connection
from modules.posts import get_post_by_id


def add_comment(post_id: int, commenter: str, message: str):
    if not get_post_by_id(post_id):
        raise ValueError(f"Post ID {post_id} not found.")
    if not commenter.strip():
        raise ValueError("Commenter name cannot be empty.")
    if not message.strip():
        raise ValueError("Comment message cannot be empty.")

    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO comments (post_id, commenter, message) VALUES (?,?,?)",
        (post_id, commenter.strip(), message.strip()),
    )
    comment_id = cur.lastrowid
    conn.commit()
    conn.close()
    return get_comment_by_id(comment_id)


def get_comment_by_id(comment_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM comments WHERE id=?", (comment_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_comments_for_post(post_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM comments WHERE post_id=? ORDER BY created_at ASC",
        (post_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_comment(comment_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()
    conn.close()


def get_comment_count(post_id: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM comments WHERE post_id=?", (post_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0
