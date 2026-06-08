# app/main.py

from fastapi import FastAPI

app = FastAPI(
    title="Task Manager API",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "message": "Task Manager API"
    }