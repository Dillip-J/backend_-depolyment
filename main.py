# main.py
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models 
import os
from routers import auth, booking, home, records, support, services, admin, admin_auth, providers, upload, users, websockets, reviews, complaints, feedback, provider_auth, meet

models.Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="V Healthcare API")

# 🚨 THE FIX 1: Turn on CORS so your frontend is legally allowed to talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your Live Server to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚨 THE FIX 2: Unlock the uploads folder so the browser can actually see the photos!
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon", status_code=204)

# (Make sure all your app.include_router(...) lines stay down here!)

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
app.include_router(provider_auth)
app.include_router(upload)
app.include_router(users)
app.include_router(websockets)
app.include_router(reviews)
app.include_router(complaints)
app.include_router(feedback)
app.include_router(meet)

@app.get("/")
def root():
    return {"status": "V Healthcare API is Online"}