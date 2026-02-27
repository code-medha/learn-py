from pydantic import BaseModel

from app.database import Base

class Post(BaseModel):
    name: str
    ram: int
    storage: int
    published: bool = True


class CreatePost(BaseModel):
    name: str
    ram: int
    storage: int
    published: bool = True

class UpdatePost(BaseModel):
    name: str
    ram: int
    storage: int
    published: bool = True      

