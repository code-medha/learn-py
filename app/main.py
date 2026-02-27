from pydoc import describe
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Response, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db


models.Base.metadata.create_all(bind=engine)

app = FastAPI()



# @app.get("/")
# def read_root():
#     return {"Hello": "sql sql sql"}

# @app.get("/sql")    
# def test_posts(db: Session = Depends(get_db)):

#     virtual_mach = db.query(models.Vm).all()
#     return {"data": virtual_mach}

@app.get(
    "/vms",
    summary="List VMs",
    description="List of virtual machines available on your cluster")
def list_vms(
    db: Session = Depends(get_db),
    page: int = Query(default=0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(default=50, ge=1, le=100, description="Records per page"),
    name: Optional[str] = Query(default=None, description="Filter by VM name")
):

    offset = page * limit
    query = db.query(models.Vm)

    if name:
        query = query.filter(models.Vm.name.contains(name))

    virtual_mach = query.offset(offset).limit(limit).all()
    return virtual_mach

@app.post(
    "/vms",
    summary="Create a VM",
    status_code=status.HTTP_201_CREATED)
def create_vm(post: schemas.CreatePost, db: Session = Depends(get_db)):
    vm_new = models.Vm(**post.model_dump())
    db.add(vm_new)
    db.commit()
    db.refresh(vm_new)

    return vm_new


# {id} is called a path parameter
@app.get("/vms/{id}")
def get_vm(id: int, db: Session = Depends(get_db)):
    vm_id = db.query(models.Vm).filter(models.Vm.id == id).first()

    if not vm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    return vm_id

@app.delete(
    "/vms/{id}",
    summary="Delete a VM")
def delete_a_vm(id: int, db: Session = Depends(get_db)):
    vm_del = db.query(models.Vm).filter(models.Vm.id == id)

    if vm_del.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")

    vm_del.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)  


@app.put(
    "/vms/{id}",
    summary="Update a VM")
def update_vm(id: int, post: schemas.UpdatePost, db: Session = Depends(get_db)):
    vm_update = db.query(models.Vm).filter(models.Vm.id == id)

    if vm_update.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")

    vm_update.update(post.model_dump(), synchronize_session=False) 
    db.commit()   

    return vm_update.first()


