from app.database.database import Base, engine

# ВАЖНО: импорт моделей ДО create_all
from app.models.user import User  # <-- ключевая строка

Base.metadata.create_all(bind=engine)

print("Database tables created")