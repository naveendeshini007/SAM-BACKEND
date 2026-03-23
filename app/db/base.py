from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic
from app.models.admins import Admins
from app.models.users import Users
from app.models.auth_events import AuthEvents
from app.models.files import Files
from app.models.sam_data import SamData