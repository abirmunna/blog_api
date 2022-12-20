from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# create db instance
def get_db():
    db = SessionLocal()
    try:
        yield db
    except:
        db.close()


@app.get("/")
def index():
    return{"<h1>Go to the /docs for api details</h1>"}
    
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session=Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered!"
        )
    return crud.create_user(db, user=user)

@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int=0, limit: int=100, db: Session=Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}",response_model=schemas.User)
def read_user(user_id: int, db: Session=Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist!"
        )
    return db_user

@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(user_id: int, item: schemas.ItemCreate, db:Session=Depends(get_db)):
    return crud.create_user_item(db=db, item=item, user_id=user_id)

@app.put("/users/{user_id}/items/{item_id}", response_model=schemas.Item)
def update_item_for_user(item_id: int,item:schemas.ItemCreate,db:Session=Depends(get_db)):
    db_item = crud.update_user_item(db, item=item, item_id=item_id)
    return db_item


@app.delete("/users/{user_id}/items/{item_id}")
def delete_item_for_user(item_id: int, db: Session=Depends(get_db)):
    res = crud.delete_user_item(db, item_id=item_id)
    if res:
        return {f"Item with id: {item_id} was deleted successfully!"}

@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items