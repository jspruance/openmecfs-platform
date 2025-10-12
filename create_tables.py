# create_tables.py
from database import Base, engine
from models import Paper  # since models.py is in the same folder

print("📦 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Done! Tables are ready.")
