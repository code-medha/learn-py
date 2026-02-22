from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class Post(BaseModel):
    name: str
    ram: int
    storage: int
    published: bool = True


@app.get("/")
def read_root():
    return {"Hello": "sql sql sql"}

@app.get("/sql")    
def test_posts(db: Session = Depends(get_db)):

    virtual_mach = db.query(models.Vm).all()
    return {"data": virtual_mach}

@app.get("/vms")
def get_posts(db: Session = Depends(get_db)):

    virtual_mach = db.query(models.Vm).all()
    return {"data": virtual_mach}

@app.post("/vms", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post, db: Session = Depends(get_db)):
    new_post = models.Vm(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {"data": new_post}



# {id} is called a path parameter
@app.get("/posts/{id}")
def get_post(id: int, response: Response):
    print(id)


    post = find_post(id)
    if not post:
        response.status_code = status.HTTP_404_NOT_FOUND
    return {"data": f"post {id}"}
