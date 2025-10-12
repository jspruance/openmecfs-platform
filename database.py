# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# 🧩 Load .env file at project root
load_dotenv()

# Example (Supabase format):
# DATABASE_URL=postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL not found in environment variables")

# 🧠 Create SQLAlchemy engine
# pool_pre_ping=True helps avoid stale connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}  # ✅ required by Supabase
)

# 🧱 Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 📘 Base model class (used by all ORM models)
Base = declarative_base()
