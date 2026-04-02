from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import dotenv
dotenv.load_dotenv()  # Load environment variables from .env file

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set! Check your .env file.")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,   # Test connection before using — prevents dead connection errors
    pool_recycle=300,     # Recycle connections every 5 min (Render closes idle ones at ~5 min)
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # 1. Configuration - Format: postgresql://user:password@host:port/dbname
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:AcademyRootPassword@localhost:5432/Eterna"

# # 2. Create the Engine
# # This is the actual connection to the database
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# # 3. Create a SessionLocal class
# # Each instance of this class will be a database session
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # 4. Create the Base class
# # Our models (User, Booking, etc.) will inherit from this class
# Base = declarative_base()

# # 5. Dependency for FastAPI
# def get_db():
#     """Provides a database session for each request and closes it after."""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
