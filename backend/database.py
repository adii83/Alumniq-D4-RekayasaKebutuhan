import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Jika ada DATABASE_URL (dari Render), gunakan itu (Postgres). 
# Jika tidak ada, gunakan SQLite lokal.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_hewTGSV2oK5a@ep-falling-voice-a12hrpdh-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

# Fix untuk Postgres di Render (ganti postgres:// jadi postgresql:// jika perlu)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite butuh check_same_thread: False, Postgres tidak.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # pool_pre_ping=True sangat penting untuk Render agar koneksi yang putus dideteksi otomatis
    # pool_recycle=1800 memastikan koneksi lama di-refresh sebelum expired
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        pool_pre_ping=True, 
        pool_recycle=1800
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
