import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from contextlib import asynccontextmanager
import psycopg2
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import AuthApiError
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
    title: str | None = None
    done: bool = False

class UserAuth(BaseModel):
    email: str | None = None
    password: str | None = None


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

@app.get("/public/info")
async def public():
    return {"message": "Welcome stranger! This info is public."}

@app.get("/protected/profile", summary="Protected route", status_code=status.HTTP_200_OK)
def get_protected_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    supabase=Depends(get_supabase)
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"},
        )

    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
    except AuthApiError as e:
            return JSONResponse(
                status_code=401,
                content={"error": e.message or "Invalid or expiredtoken"},
            )
    return {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": response.user.created_at,
    }



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
def create_task(task: TaskCreate, db=Depends(get_db)):
    if not task.title:
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"},
        )
    return repo_create_task(db, task["title"], task.get("done", False))


@app.post("/auth/signup", summary="Sign users up", status_code=status.HTTP_201_CREATED)
def sign_up(user: UserAuth, supabase=Depends(get_supabase)):
    if not user.email or not user.password:
        return JSONResponse(
            status_code=400,
            content={"error": "User email or password is required"},
        )
    response = supabase.auth.sign_up(
        {
            "email": user.email,
            "password": user.password,
        }
    )
    return response

@app.post("/auth/login", summary="Login Users", status_code=status.HTTP_200_OK)
def login(user: UserAuth, supabase=Depends(get_supabase)):
    if not user.email or not user.password:
        return JSONResponse(
            status_code=400,
            content={"error": "User email or password is required"},
        )
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": user.password,
            }
        )
    except AuthApiError as e:
        return JSONResponse(
            status_code=401,
            content={"error": e.message or "Invalid email or password"},
        )
    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }


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