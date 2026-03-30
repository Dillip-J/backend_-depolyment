# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Import StaticFiles
from database import engine, Base
import models # Needed to create the uploads folder safely
import os
from fastapi import Response
from routers import auth, booking, home, records, support, services, admin, admin_auth, providers, upload, users, websockets, reviews, complaints 
# Initialize Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="V Healthcare API")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon", status_code=204)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
# This tells FastAPI: "If a URL starts with /uploads, look in the uploads folder"
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Connect Routers
app.include_router(auth)
app.include_router(home)
app.include_router(services)
app.include_router(booking)
app.include_router(records)
app.include_router(support)
app.include_router(admin)
app.include_router(admin_auth)
app.include_router(providers)
app.include_router(upload)
app.include_router(users)
app.include_router(websockets)
app.include_router(reviews)
app.include_router(complaints)
@app.get("/")
def root():
    return {"status": "V Healthcare API is Online"}

# # Connect Routers
# app.include_router(auth.router)
# app.include_router(home.router)
# app.include_router(services.router)
# app.include_router(booking.router)
# app.include_router(records.router)
# app.include_router(support.router)
# app.include_router(admin.router)
# app.include_router(admin_auth.router)
# app.include_router(providers.router)
# app.include_router(upload.router)
# app.include_router(users.router)
# app.include_router(websockets.router)
    
# import logging
# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from models import user
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn

# # 1. Import Database Engine and Base
# from database import engine, Base
# import models  # This ensures all models are loaded before table creation

# # 2. Import actual Healthcare routers
# from models import services
# from routers import (
#     auth,
#     booking,
#     home, 
#     records, 
#     support, 
#     websockets
# )

# # Logging Configuration
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Lifespan (Startup & Shutdown)
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # --- Startup ---
#     logger.info("🚀 Starting V (Vision) Healthcare API...")
    
#     try:
#         # 3. Create Tables automatically if they don't exist
#         logger.info("🛠️ Creating/Updating Database Tables...")
#         Base.metadata.create_all(bind=engine)
#         logger.info("✅ Database initialized successfully")
#     except Exception as e:
#         logger.error(f"❌ Database initialization failed: {e}")

#     yield  # Application runs here

#     # --- Shutdown ---
#     logger.info("🛑 Shutting down V (Vision) Healthcare API")

# # App Initialization
# app = FastAPI(
#     title="V (Vision) Healthcare API",
#     description="Convenient and Time-Efficient Healthcare",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS Middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Routers Registration
# app.include_router(auth.router)
# app.include_router(home.router)
# app.include_router(services.router)
# app.include_router(booking.router)
# app.include_router(records.router)
# app.include_router(support.router)
# app.include_router(websockets.router)

# @app.get("/")
# def root():
#     return {
#         "message": "V (Vision) Healthcare API is running",
#         "status": "healthy",
#         "orm": "SQLAlchemy Enabled"
#     }

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)