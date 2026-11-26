
from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routes import students, resumes, recommendations

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="AI Career Companion",
    description="AI-powered internship application assistant",
    version="1.0.0"
)

# Register student API routes
app.include_router(students.router)
app.include_router(resumes.router)
app.include_router(recommendations.router)


@app.get("/")
def home():
    return {
        "message": "AI Career Companion API is running",
        "milestone": "M2.3 - Job-Resume Matching Agent",
        "status": "success"
    }
