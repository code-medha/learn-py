from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool


@app.get("/")
def read_root():
    return {"Hello": "sql sql sql"}

@app.get("/sql")    
def test_posts(db: Session = Depends(get_db)):
    return {"status": "success"}

@app.get("/posts")
def get_posts():
    return {"data": "this is your posts"}

@app.post("/posts")
def create_posts(post: Post):
    print(post)
    return {"message": "post created"}


# {id} is called a path parameter
@app.get("/posts/{id}")
def get_post(id: int, response: Response):
    print(id)


    post = find_post(id)
    if not post:
        response.status_code = status.HTTP_404_NOT_FOUND
    return {"data": f"post {id}"}
