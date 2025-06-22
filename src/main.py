from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

app = FastAPI(title="Mentor API", description="AI Mentors for Student Learning", version="1.0.0")

# Add CORS middleware FIRST, before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["https://mentor-vibes.netlify.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
