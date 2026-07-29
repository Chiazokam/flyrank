"""
Simple Task API built with FastAPI.

Provides 5 endpoints to manage an in-memory collection of tasks:
    - GET    /tasks          -> list all tasks
    - GET    /tasks/{id}     -> get one task
    - POST   /tasks          -> create a task
    - PUT    /tasks/{id}     -> update a task
    - DELETE /tasks/{id}     -> delete a task

No database is used; tasks live in a plain Python list in memory,
so data resets whenever the app restarts.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    description="A minimal CRUD API for managing tasks (in-memory, no database).",
    version="1.0.0",
)
# Swagger UI is available at the default /docs URL, using FastAPI's
# standard CDN-hosted assets.


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Task(BaseModel):
    id: int
    title: str
    done: bool = False


class TaskCreate(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------------
# Initial in-memory data
# ---------------------------------------------------------------------------
tasks: list[dict] = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Write project proposal", "done": True},
    {"id": 3, "title": "Clean the house", "done": False},
    {"id": 4, "title": "Read a book", "done": False},
    {"id": 5, "title": "Schedule dentist appointment", "done": True},
]

# Tracks the next id to assign to a newly created task.
_next_id = max(task["id"] for task in tasks) + 1


def _find_task(task_id: int) -> Optional[dict]:
    """Return the task dict matching task_id, or None if not found."""
    return next((task for task in tasks if task["id"] == task_id), None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/tasks",
    response_model=list[Task],
    summary="Get all tasks",
    description="Retrieve the full list of tasks currently stored in memory.",
)
def get_tasks():
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get one task",
    description="Retrieve a single task by its id. Returns a 404 error "
    "with `{\"error\": \"Task {id} not found\"}` if the id does not exist.",
)
def get_task(task_id: int):
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"},
        )
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description="Create a new task. A `title` is required; if it is missing "
    "or empty, a 400 error is returned with "
    "`{\"error\": \"Title must have a value\"}`.",
)
def create_task(task: TaskCreate):
    global _next_id

    if not task.title or not task.title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title must have a value"},
        )

    new_task = {"id": _next_id, "title": task.title, "done": task.done}
    tasks.append(new_task)
    _next_id += 1
    return new_task


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task",
    description="Update an existing task's title and/or done status. "
    "Returns a 404 error with `{\"error\": \"Task {id} not found\"}` "
    "if the id does not exist.",
)
def update_task(task_id: int, task_update: TaskUpdate):
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"},
        )

    if task_update.title is not None:
        task["title"] = task_update.title
    if task_update.done is not None:
        task["done"] = task_update.done

    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete a task by its id. Returns a 404 error with "
    "`{\"error\": \"Task {id} not found\"}` if the id does not exist. "
    "On success, returns a 204 No Content response.",
)
def delete_task(task_id: int):
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"},
        )

    tasks.remove(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
