#!/usr/bin/env python3
"""
Main entry point for the Video Upload API
Simple FastAPI server for uploading videos to Docker container
"""

import uvicorn
from api.endpoints import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="Video Upload API",
    description="Simple API for uploading videos to Docker container",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Video Upload API",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "upload": "/api/v1/upload",
            "list_videos": "/api/v1/videos",
            "container_status": "/api/v1/container/status",
        },
    }


def main():
    """Run the FastAPI server"""
    print("Starting Video Upload API...")
    print("API will be available at: http://localhost:8002")
    print("Make sure your Docker container is running: docker-compose up -d")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,  # Enable hot reload for development
        log_level="info",
    )


if __name__ == "__main__":
    main()
