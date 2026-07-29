from fastapi import Depends, FastAPI, status
from contextlib import asynccontextmanager
import sqlite3
from fastapi.responses import JSONResponse
from pydantic import BaseModel

DB = "tasks.db"

class TaskCreate(BaseModel):
    title: str
    done: bool = False

tasks = [
    {
        "id": 1,
        "title": "Task 1",
        "done": False
    },
    {
        "id": 2,
        "title": "Task 2",
        "done": False
    },
    {
        "id": 3,
        "title": "Task 3",
        "done": True
    }
]

def connect_db():
    # check_same_thread=False is required for SQLite to work safely with FastAPI's multithreading
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries instead of tuples
    return conn

def get_db():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()

# @asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    conn = connect_db()
    cursor = conn.cursor()

    # 1. Create the table if it doesn't already exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT False
        )
        """
    )

    # 2. Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    # 3. Insert three example tasks ONLY if empty
    if count == 0:
        example_tasks = [
            ("Set up FastAPI project", False),
            ("Connect SQLite database", False),
            ("Build task management API", True),
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            example_tasks,
        )
        conn.commit()

    conn.close()

    yield

app = FastAPI(title="Tasky", lifespan=lifespan)

@app.get("/")
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks", summary="Retrieve all tasks")
def get_tasks(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = [{**dict(row), "done": bool(row["done"])} for row in cursor.fetchall()]
    return tasks

@app.get("/tasks/{id}", summary="Retrieve a task by ID", status_code=status.HTTP_200_OK)
def get_task(id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
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
        return { "error": "Title is required" }, 400

    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, completed) VALUES (?, ?)",
        (task.title, task.done),
    )
    db.commit()
    
    # Fetch the newly created task
    task_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    new_task = cursor.fetchone()
    
    return new_task, 201
    

@app.put("/tasks/{id}", summary="Update a task by ID", status_code=status.HTTP_200_OK)
def update_task(id: int, task: dict, db=Depends(get_db)):
    cursor = db.cursor()
    
    # Check if task exists
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    existing_task = cursor.fetchone()
    
    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )
    
    cursor.execute(
        "UPDATE tasks SET title = ?, completed = ? WHERE id = ?",
        (task.title, task.completed, id),
    )
    db.commit()
    
    # Fetch and return the updated task
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    updated_task = cursor.fetchone()
    
    return dict(updated_task)
    
@app.delete("/tasks/{id}", summary="Delete a task by ID", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db=Depends(get_db)):
    cursor = db.cursor()
    
    # Check if task exists
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    existing_task = cursor.fetchone()
    
    if existing_task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )
    
    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
    db.commit()
    
    return {"message": "Task deleted successfully"}
