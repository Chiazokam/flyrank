# Task API

A minimal Task management API built with **Python** and **FastAPI**. Tasks are
stored in a plain in-memory Python list — no database is used, so data resets
whenever the app restarts.

## Endpoints

| Method | Path            | Description             | Success | Error(s)                                  |
|--------|-----------------|--------------------------|---------|--------------------------------------------|
| GET    | `/tasks`        | Get all tasks            | 200     | —                                          |
| GET    | `/tasks/{id}`   | Get one task             | 200     | 404 `{"error": "Task {id} not found"}`     |
| POST   | `/tasks`        | Create a task             | 201     | 400 `{"error": "Title must have a value"}` |
| PUT    | `/tasks/{id}`   | Update a task             | 200     | 404 `{"error": "Task {id} not found"}`     |
| DELETE | `/tasks/{id}`   | Delete a task             | 204     | 404 `{"error": "Task {id} not found"}`     |

Each task looks like:

```json
{
  "id": 1,
  "title": "Buy groceries",
  "done": false
}
```

The app starts with 5 sample tasks pre-loaded.

## Running locally

```bash
python -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Interactive docs

FastAPI automatically generates interactive Swagger UI docs at `/docs`
(and ReDoc at `/redoc`). Each endpoint includes a summary and description,
including the error responses it can return.

**http://127.0.0.1:8000/docs**

![Swagger UI docs](docs_screenshot.png)

## Example requests

```bash
# Get all tasks
curl http://127.0.0.1:8000/tasks

# Get one task
curl http://127.0.0.1:8000/tasks/1

# Create a task
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Walk the dog"}'

# Update a task
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"done": true}'

# Delete a task
curl -X DELETE http://127.0.0.1:8000/tasks/1
```
