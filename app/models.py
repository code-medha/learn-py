# every models represents a table in our database

from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Vm(Base):
     __tablename__ = "vm"

     id = Column(Integer, primary_key=True, nullable=False)
     name = Column(String, nullable=False)
     ram = Column(Integer, nullable=False)
     storage = Column(Integer, nullable=False)
     published = Column(Boolean,)
