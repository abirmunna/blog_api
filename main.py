from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
test = HTTPBearer()

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

@AuthJWT.load_config
def get_config():
    return schemas.Settings()

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

@app.get("/")
def index():
    return{"<h1>Go to the /docs for api details</h1>"}

@app.post("/login", tags=["login"])
def login(user: schemas.UserLogin, db: Session=Depends(get_db), Authorize: AuthJWT=Depends()):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist!"
        )
    if not db_user.hashed_password == user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password!"
        )
    access_token = Authorize.create_access_token(subject=db_user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User, tags=["users"])
def create_user(user: schemas.UserCreate, db: Session=Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered!"
        )
    return crud.create_user(db, user=user)

@app.get("/users/", response_model=list[schemas.User], tags=["users"])
def read_users(skip: int=0, limit: int=100, db: Session=Depends(get_db),
Authorize: AuthJWT = Depends(),credentials: HTTPAuthorizationCredentials = Security(test)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/user/",response_model=schemas.User, tags=["users"])
def read_user(db: Session=Depends(get_db),
Authorize: AuthJWT = Depends(),credentials: HTTPAuthorizationCredentials = Security(test)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist!"
        )
    return db_user

@app.post("/user/{user_id}/item/", response_model=schemas.Item, tags=["items"])
def create_item_for_user(item: schemas.ItemCreate, db:Session=Depends(get_db),
Authorize: AuthJWT = Depends(),credentials: HTTPAuthorizationCredentials = Security(test)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    return crud.create_user_item(db=db, item=item, user_id=user_id)

@app.put("/user/item/{item_id}", response_model=schemas.Item, tags=["items"])
def update_item_for_user(item_id: int,item:schemas.ItemCreate,db:Session=Depends(get_db),
Authorize: AuthJWT = Depends(),credentials: HTTPAuthorizationCredentials = Security(test)):
    db_item = crud.update_user_item(db, item=item, item_id=item_id)
    return db_item


@app.delete("/user/item/{item_id}", tags=["items"])
def delete_item_for_user(item_id: int, db: Session=Depends(get_db),
Authorize: AuthJWT = Depends(),credentials: HTTPAuthorizationCredentials = Security(test)):
    res = crud.delete_user_item(db, item_id=item_id)
    if res:
        return {f"Item with id: {item_id} was deleted successfully!"}

@app.get("/items/", response_model=list[schemas.Item], tags=["items"])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
Authorize: AuthJWT = Depends(),credentials: HTTPAuthorizationCredentials = Security(test)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
    