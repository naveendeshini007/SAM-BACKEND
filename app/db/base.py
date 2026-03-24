from sqlalchemy.orm import declarative_base

Base = declarative_base()

#Imports all the models from Alembic
# from app.models.admin import Admin
# from app.models.files import Files
# from app.models.sam_data import SamData

import app.models.admin
import app.models.files
import app.models.sam_data