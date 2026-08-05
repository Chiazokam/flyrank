from psycopg2.extras import RealDictCursor


def create_task(db, title, done=False):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
        (title, done),
    )
    db.commit()
    task_id = cursor.fetchone()["id"]
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    return dict(cursor.fetchone())


def get_all_tasks(db):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tasks")
    return [{**row, "done": bool(row["done"])} for row in cursor.fetchall()]


def get_task_by_id(db, task_id):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    if task is None:
        return None
    return dict(task)


def update_task(db, task_id, title=None, done=None):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    existing = cursor.fetchone()
    if existing is None:
        return None

    new_title = title if title is not None else existing["title"]
    new_done = done if done is not None else existing["done"]

    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (new_title, new_done, task_id),
    )
    db.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    return dict(cursor.fetchone())


def delete_task(db, task_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    existing = cursor.fetchone()
    if existing is None:
        return False

    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    db.commit()
    return True