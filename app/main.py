from fastapi import FastAPI, Response, status
from pydantic import BaseModel

app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool


def find_post(id):
    pass

@app.get("/")
def read_root():
    return {"Hello": "sql sql sql"}

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
