from pydantic import BaseModel, Field

from app.database import Base

class Post(BaseModel):
    name: str
    ram: int
    storage: int
    published: bool = True


class CreatePost(BaseModel):
    name: str = Field(..., description="VM name.", max_length=80)
    ram: int = Field(..., description="Memory size in GB.")
    storage: int = Field(..., description="Storage size in GB.")
    published: bool = Field(default=True, description="Whether the VM is published and visible to users.")

class UpdatePost(BaseModel):
    name: str
    ram: int
    storage: int
    published: bool = True      

