from fastapi import FastAPI

app = FastAPI(title="Tasky")

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

@app.get("/")
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{id}")
def get_task(id: int):
    task = next((task for task in tasks if task["id"] == id), None)
    if task:
        return task
    else:
        return  { "error": f"Task {id} not found" }, 404

@app.post("/tasks")
def create_task(task: dict):
    if "title" not in task:
        return { "error": "Title is required" }, 400

    else:
        new_task = {
        "id": len(tasks) + 1,
        "title": task["title"],
        "done": False
        }
        tasks.append(new_task)
        return new_task, 201
    