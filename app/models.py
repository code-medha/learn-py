# every models represents a table in our database


from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean, text
from sqlalchemy.sql.functions import now
from .database import Base

class Vm(Base):
     __tablename__ = "vm"

     id = Column(Integer, primary_key=True, nullable=False)
     name = Column(String, nullable=False)
     ram = Column(Integer, nullable=False)
     storage = Column(Integer, nullable=False)
     published = Column(Boolean,server_default='TRUE', nullable=False)
     created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
