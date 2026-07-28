# Tasky

A small REST API for managing tasks, built with [FastAPI](https://fastapi.tiangolo.com/). Tasks are stored in memory (no database) and seeded with three sample items on startup. The app exposes CRUD endpoints for listing, creating, updating, and deleting tasks, plus a health check route.

## Install & run

From the `tasky/` directory:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload
```

The server listens at http://127.0.0.1:8000. Interactive API docs are at http://127.0.0.1:8000/docs.

## Endpoints

| Method | Path | Summary | Request body | Success response |
|--------|------|---------|--------------|------------------|
| `GET` | `/` | Service metadata | — | `200` — `{ "name", "version", "endpoints" }` |
| `GET` | `/health` | Health check | — | `200` — `{ "status": "ok" }` |
| `GET` | `/tasks` | List all tasks | — | `200` — array of tasks |
| `GET` | `/tasks/{id}` | Get task by ID | — | `200` — task object; `404` if not found |
| `POST` | `/tasks` | Create a task | `{ "title": string }` | `201` — new task; `400` if title missing |
| `PUT` | `/tasks/{id}` | Update a task | `{ "title"?: string, "done"?: bool }` | `200` — updated task; `404` if not found |
| `DELETE` | `/tasks/{id}` | Delete a task | — | `204` — deleted; `404` if not found |

Task object shape:

```json
{ "id": 1, "title": "Task 1", "done": false }
```

## Example request

```bash
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy coke"}'
```

```
HTTP/1.1 200 OK
date: Tue, 28 Jul 2026 17:45:07 GMT
server: uvicorn
content-length: 46
content-type: application/json

[{"id":4,"title":"Buy coke","done":false},201]
```

## Docs

Visit http://localhost:8000/docs to see the the docs

![Swagger](./screenshots/swagger.png)