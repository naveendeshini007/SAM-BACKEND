from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic

# from app.models.admins import Admin
# from app.models.files import Files
# from app.models.sam_data import SamData
import app.models.admin
import app.models.files
import app.models.sam_data