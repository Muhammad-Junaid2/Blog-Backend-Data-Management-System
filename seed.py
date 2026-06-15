"""
Seed the database with sample data for demo purposes.
"""
from modules.database import init_db
from modules.users import register_user
from modules.posts import create_post, react_to_post
from modules.comments import add_comment


SAMPLE_USERS = [
    ("admin",   "admin@blog.com",   "Admin@123",   "admin"),
    ("alice",   "alice@blog.com",   "Alice@123",   "user"),
    ("bob",     "bob@blog.com",     "Bob@123",     "user"),
    ("charlie", "charlie@blog.com", "Charlie@123", "user"),
]

SAMPLE_POSTS = [
    (
        "Getting Started with Python",
        """Python is one of the most popular programming languages in the world, and for good reason.
Its clean syntax makes it easy to read and write, while its vast ecosystem of libraries
makes it suitable for everything from web development to machine learning.

In this post, we'll cover the basics you need to get up and running quickly:
- Installing Python
- Setting up a virtual environment
- Writing your first script
- Understanding Python's data types

Whether you're a complete beginner or coming from another language, Python's
gentle learning curve will have you productive in no time.""",
        "alice", "Python", "python,beginner,programming"
    ),
    (
        "10 Tips for Writing Clean Code",
        """Writing clean code is a skill that separates good developers from great ones.
Here are ten battle-tested tips that will transform the quality of your codebase:

1. Use meaningful variable names — avoid single letters except in loops.
2. Keep functions short — aim for under 20 lines per function.
3. Write comments that explain WHY, not WHAT.
4. Follow the DRY principle: Don't Repeat Yourself.
5. Use consistent formatting and follow your language's style guide.
6. Write tests — untested code is broken code you haven't found yet.
7. Refactor regularly — don't let technical debt accumulate.
8. Handle errors gracefully — never swallow exceptions silently.
9. Use version control and commit often with meaningful messages.
10. Review your own code before asking others to review it.

Clean code is not about being clever. It's about being clear.""",
        "bob", "Software Engineering", "clean code,best practices,tips"
    ),
    (
        "Introduction to SQLite with Python",
        """SQLite is a lightweight, serverless relational database that's perfect for
small-to-medium applications. Unlike PostgreSQL or MySQL, it requires zero
configuration and stores your entire database in a single file.

Python ships with SQLite support built right in — no installation needed.
Just import sqlite3 and you're ready to go.

Key advantages of SQLite:
- Zero configuration required
- Single file storage — easy to backup and share
- ACID compliant — your data is safe
- Surprisingly fast for most use cases
- Perfect for prototyping before migrating to a heavier DB

In this tutorial, we'll build a simple CRUD application using Python's
sqlite3 module and explore connection management, parameterized queries,
and row factories.""",
        "alice", "Databases", "sqlite,database,python"
    ),
    (
        "Building Your First REST API",
        """REST APIs are the backbone of modern web applications. Whether you're building
a mobile app, a single-page application, or a microservice, chances are you'll
need to design and implement a REST API.

In this guide, we'll cover:
- REST principles and HTTP methods
- Designing clean, intuitive endpoints
- Status codes and error handling
- Authentication with JWT tokens
- Rate limiting and security best practices

We'll use Python's Flask framework for our examples, but the concepts apply
to any language or framework. By the end, you'll have a working API you can
deploy to production.""",
        "charlie", "Web Development", "api,rest,flask,python"
    ),
    (
        "Understanding Async Programming",
        """Asynchronous programming has become essential in modern software development.
When your application needs to handle thousands of concurrent connections,
traditional synchronous code just doesn't cut it anymore.

Python's asyncio library, introduced in Python 3.4 and significantly improved
in later versions, gives us powerful tools for writing non-blocking code.

The key concepts we'll explore:
- The event loop and how it works
- async/await syntax explained simply
- Coroutines vs threads vs processes
- Common pitfalls and how to avoid them
- Real-world example: async HTTP client

Once you understand async programming, you'll wonder how you ever lived without it.""",
        "bob", "Python", "async,asyncio,concurrency"
    ),
    (
        "Why Documentation Matters",
        """Documentation is often an afterthought — something developers write reluctantly
after the code is done. But good documentation is as important as good code.

Consider this: you'll spend more time reading code than writing it. Your future
self — six months from now — will thank you for writing clear docs today.

Great documentation includes:
- A clear README with setup instructions
- API reference generated from docstrings
- Tutorials for common use cases
- A changelog tracking major changes
- Architecture diagrams for complex systems

Tools like Sphinx, MkDocs, and pdoc make it easier than ever to generate
beautiful documentation from your Python docstrings automatically.""",
        "charlie", "Best Practices", "documentation,devops,writing"
    ),
]

SAMPLE_COMMENTS = [
    (1, "John",    "Great introduction! Really helped me get started."),
    (1, "Sarah",   "I've been looking for exactly this kind of guide. Thanks!"),
    (2, "Mike",    "Tip #6 about testing is so important. Learned that the hard way."),
    (2, "Lisa",    "Would add: use a linter and formatter automatically in CI."),
    (3, "Dave",    "SQLite is underrated for small projects. Great write-up!"),
    (4, "Emma",    "Can you do a follow-up on authentication? JWT section was brief."),
    (5, "Carlos",  "async/await clicked for me after reading this. Thank you!"),
    (6, "Priya",   "Documentation saved me so many hours debugging legacy code."),
]


def seed():
    init_db()
    print("🌱 Seeding database with sample data...")

    users = {}
    for username, email, password, role in SAMPLE_USERS:
        try:
            u = register_user(username, email, password, role)
            users[username] = u
            print(f"  ✅ User: {username} ({role})")
        except ValueError as e:
            if "already exists" in str(e):
                from modules.users import get_user_by_username
                u = get_user_by_username(username)
                if u:
                    users[username] = u
                print(f"  ⚠️  User {username} already exists, skipping.")
            else:
                print(f"  ❌ User {username}: {e}")

    posts = []
    for title, content, author_name, category, tags in SAMPLE_POSTS:
        try:
            author = users.get(author_name)
            if not author:
                print(f"  ❌ Author {author_name} not found, skipping post.")
                continue
            p = create_post(title, content, author["id"], category, tags)
            posts.append(p)
            print(f"  ✅ Post: {title[:50]}...")
        except Exception as e:
            print(f"  ❌ Post '{title[:30]}': {e}")

    for post_id, commenter, message in SAMPLE_COMMENTS:
        if post_id <= len(posts):
            try:
                add_comment(posts[post_id - 1]["id"], commenter, message)
            except Exception:
                pass

    # Add some reactions
    try:
        react_to_post(posts[0]["id"], users["alice"]["id"], "like")
        react_to_post(posts[0]["id"], users["bob"]["id"], "like")
        react_to_post(posts[1]["id"], users["alice"]["id"], "like")
        react_to_post(posts[2]["id"], users["charlie"]["id"], "like")
        react_to_post(posts[3]["id"], users["bob"]["id"], "dislike")
    except Exception:
        pass

    print("\n✅ Seeding complete! Database is ready.")


if __name__ == "__main__":
    seed()
