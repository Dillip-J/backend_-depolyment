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
try:
    os.makedirs("uploads", exist_ok=True)
    # This tells FastAPI: "If a URL starts with /uploads, look in the uploads folder"
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except OSError:
    print("Warning: Running on a read-only filesystem (e.g., Vercel). Local uploads directory could not be created.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
 