from fastapi import FastAPI

app = FastAPI(title="Tasky")


@app.get("/")
async def root():
    return {"message": "Hello World"}
