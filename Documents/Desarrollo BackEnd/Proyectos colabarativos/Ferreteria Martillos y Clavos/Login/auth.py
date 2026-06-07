from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

SECRET_KEY = "bb6787df2be4f80a700e6dbcdf9cbec6"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pass_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str):
    return pass_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str):
    return pass_context.verify(plain_password, hashed_password)

def verify_user_database(db: Session, username: str, password: str):
    db_user = db.query(User).filter(User.username == username).first()
    db_password = db.query(User).filter(User.password == password).first()
    if not db_user or not db_password:
        return None
    return {"id": db_user.id, "username": db_user.username}

def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

"""def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm=["ALGORITHM"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")"""

def get_current_user(db, access_token):
    try:
        token = access_token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_actual = payload.get("sub")
        user_db = db.query(User).filter(User.username == username_actual).first()
        return user_db
    except jwt.PyJWTError:
        return None