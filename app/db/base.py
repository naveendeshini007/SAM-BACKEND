from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic

from app.models.admin import Admin