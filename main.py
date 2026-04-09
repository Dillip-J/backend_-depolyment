# main.py
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models 
import os
from routers import auth, booking, home, records, support, services, admin, admin_auth, providers, upload, users, websockets, reviews, complaints, feedback

# Initialize Database Tables
models.Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="V Healthcare API")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon", status_code=204)

# ONLY MOUNT ONCE (Using the safe try/except block) 
try:
    os.makedirs("uploads", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except OSError:
    print("Warning: Running on a read-only filesystem (e.g., Vercel). Local uploads directory could not be created.")

#  CORS MIDDLEWARE 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Lets your frontend talk to the backend
    allow_credentials=True,      # Allows cookies/tokens
    allow_methods=["*"],         # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],         # Allows all headers (like Authorization)
)

# ==========================================
# 🚨 THE GUARANTEED DB FIX ROUTE 🚨
# ==========================================
@app.get("/fix-db")
def fix_database_sync(db: Session = Depends(get_db)):
    try:
        # 1. Inject missing columns into the existing 'users' table
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS latitude NUMERIC(10, 8);"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS longitude NUMERIC(11, 8);"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS saved_address TEXT;"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        
        # 2. Inject missing columns into 'admins' table
        db.execute(text("ALTER TABLE admins ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))

        # 3. Inject the entirely new 'saved_addresses' table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_addresses (
                address_id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                label VARCHAR(50) NOT NULL,
                address_text TEXT NOT NULL,
                latitude NUMERIC(10, 8),
                longitude NUMERIC(11, 8),
                is_default BOOLEAN DEFAULT FALSE
            );
        """))
        
        db.commit()
        return {"message": "✅ Database fully synced with new columns and tables!"}
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

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
app.include_router(feedback)

@app.get("/")
def root():
    return {"status": "V Healthcare API is Online"}
# # main.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles # Import StaticFiles
# from database import engine, Base
# import models # Needed to create the uploads folder safely
# import os
# from fastapi import Response
# from routers import auth, booking, home, records, support, services, admin, admin_auth, providers, upload, users, websockets, reviews, complaints, feedback
# # Initialize Database Tables
# models.Base.metadata.create_all(bind=engine)
 
# app = FastAPI(title="V Healthcare API")
 
# @app.get("/favicon.ico", include_in_schema=False)
# async def favicon():
#     return Response(content="", media_type="image/x-icon", status_code=204)

# # Create uploads directory if it doesn't exist
# try:
#     os.makedirs("uploads", exist_ok=True)
#     # This tells FastAPI: "If a URL starts with /uploads, look in the uploads folder"
#     app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# except OSError:
#     print("Warning: Running on a read-only filesystem (e.g., Vercel). Local uploads directory could not be created.")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5500",
#         "http://127.0.0.1:5500",
#         "http://localhost:3000",
#         "http://127.0.0.1:3000",
#         "http://localhost:8080",
#         "http://127.0.0.1:8080",
#         "file://",  # Allow local HTML file opens
#         # Add your deployed GitHub Pages / Vercel URL here:
#         # "https://your-username.github.io",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Connect Routers
# app.include_router(auth)
# app.include_router(home)
# app.include_router(services)
# app.include_router(booking)
# app.include_router(records)
# app.include_router(support)
# app.include_router(admin)
# app.include_router(admin_auth)
# app.include_router(providers)
# app.include_router(upload)
# app.include_router(users)
# app.include_router(websockets)
# app.include_router(reviews)
# app.include_router(complaints)
# app.include_router(feedback)


# @app.get("/")
# def root():
#     return {"status": "V Healthcare API is Online"}
 