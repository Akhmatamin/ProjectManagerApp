from fastapi import FastAPI
import uvicorn
from app.auth.router import auth_router
app = FastAPI(title="Project Manager API", description="API for managing projects, users, and documents.")

app.include_router(auth_router)

@app.get("/")
def get_page():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)