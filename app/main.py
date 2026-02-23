from fastapi import Depends, FastAPI, HTTPException, Response, status
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
    return {virtual_mach}

@app.post("/vms", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post, db: Session = Depends(get_db)):
    new_post = models.Vm(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {new_post}


# {id} is called a path parameter
@app.get("/posts/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post_id = db.query(models.Vm).filter(models.Vm.id == id).first()

    if not post_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    return {post_id}

@app.delete("/posts/{id}")
def delete_post(id: int, db: Session = Depends(get_db)):
    post_del = db.query(models.Vm).filter(models.Vm.id == id)

    if post_del.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")

    post_del.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)   


