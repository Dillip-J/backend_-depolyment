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
# This tells FastAPI to allow the browser to see files in the 'uploads' folder
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "V Healthcare API is Online"}
 

 

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
