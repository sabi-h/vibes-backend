from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

app = FastAPI(title="Mentor API", description="AI Mentors for Student Learning", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
