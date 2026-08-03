import os
from fastapi import Depends, FastAPI, status
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

DB = database_url


class TaskCreate(BaseModel):
    title: str
    done: bool = False


def connect_db():
    conn = psycopg2.connect(DB)
    return conn


def get_db():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT False
        )
        """
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        example_tasks = [
            ("Set up FastAPI project", False),
            ("Connect SQLite database", False),
            ("Build task management API", True),
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            example_tasks,
        )
        conn.commit()

    conn.close()
    yield


app = FastAPI(title="Tasky", lifespan=lifespan)


@app.get("/")
async def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="Retrieve all tasks")
def get_tasks(db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tasks")
    tasks = [{**row, "done": bool(row["done"])} for row in cursor.fetchall()]
    return tasks


@app.get("/tasks/{id}", summary="Retrieve a task by ID", status_code=status.HTTP_200_OK)
def get_task(id: int, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cursor.fetchone()

    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )

    return dict(task)


@app.post("/tasks", summary="Create a new task", status_code=status.HTTP_201_CREATED)
def create_task(task: dict, db=Depends(get_db)):
    if "title" not in task:
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"},
        )

    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
        (task["title"], task.get("done", False)),
    )
    db.commit()

    task_id = cursor.fetchone()["id"]
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    new_task = cursor.fetchone()

    return dict(new_task)


@app.put("/tasks/{id}", summary="Update a task by ID", status_code=status.HTTP_200_OK)
def update_task(id: int, task: dict, db=Depends(get_db)):
    cursor = db.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    existing_task = cursor.fetchone()

    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )

    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (task.get("title", existing_task["title"]),
         task.get("done", existing_task["done"]), id),
    )
    db.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    updated_task = cursor.fetchone()

    return dict(updated_task)


@app.delete("/tasks/{id}", summary="Delete a task by ID", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db=Depends(get_db)):
    cursor = db.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    existing_task = cursor.fetchone()

    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )

    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    db.commit()

    return Response(status_code=204)
