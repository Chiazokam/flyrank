import os
from fastapi import Depends, FastAPI, status
from contextlib import asynccontextmanager
import psycopg2
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import Client
from database import get_supabase

from repository import (
    create_task as repo_create_task,
    get_all_tasks as repo_get_all_tasks,
    get_task_by_id as repo_get_task_by_id,
    update_task as repo_update_task,
    delete_task as repo_delete_task,
)

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
    return repo_get_all_tasks(db)


@app.get("/tasks/{id}", summary="Retrieve a task by ID", status_code=status.HTTP_200_OK)
def get_task(id: int, db=Depends(get_db)):
    task = repo_get_task_by_id(db, id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )
    return task


@app.post("/tasks", summary="Create a new task", status_code=status.HTTP_201_CREATED)
def create_task(task: dict, db=Depends(get_db)):
    if "title" not in task:
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"},
        )
    return repo_create_task(db, task["title"], task.get("done", False))


@app.put("/tasks/{id}", summary="Update a task by ID", status_code=status.HTTP_200_OK)
def update_task(id: int, task: dict, db=Depends(get_db)):
    updated = repo_update_task(db, id, task.get("title"), task.get("done"))
    if updated is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )
    return updated


@app.delete("/tasks/{id}", summary="Delete a task by ID", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, db=Depends(get_db)):
    deleted = repo_delete_task(db, id)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"},
        )
    return Response(status_code=204)