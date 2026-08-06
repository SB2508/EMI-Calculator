import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Set DATABASE_URL as an env var when you deploy, e.g.:
# postgresql://user:password@host:5432/emi_calculator   (Render)
# mysql+pymysql://user:password@host:3306/emi_calculator (Railway/other MySQL)
# Falls back to local SQLite so you can develop without a real DB set up yet.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./emi_calculator.db")

# Render (and some other hosts) hand out URLs starting with "postgres://",
# but SQLAlchemy 1.4+ requires the "postgresql://" scheme. Fix it automatically.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
