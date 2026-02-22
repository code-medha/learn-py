from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:password@db:5432/virtual'

# establish connection
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# when you want to talk to the sql database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# models extend the base class
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()       



