from fastapi import FastAPI
from app.api import auth

app = FastAPI(title="Task Manager API")

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Task Manager API"}