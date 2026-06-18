from fastapi import APIRouter, Depends, HTTPException, Request, Form, Cookie
from sqlalchemy.orm import Session
from Core.database import get_db
from .models import User
from .auth import hash_password, verify_password, create_access_token, get_current_user, verify_user_database
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse(request, "index_login.html")

@router.get("/login", response_class=HTMLResponse)
def view_login(request: Request):
    return templates.TemplateResponse(request, "login.html")

@router.get("/sign up", response_class=HTMLResponse)
def view_sign_up(request: Request):
    return templates.TemplateResponse(request, "sign_up.html")

@router.get("/view", response_class=HTMLResponse)
def get_profile(request: Request, db: Session = Depends(get_db), access_token: str = Cookie(None)):
    user_actual = get_current_user(db, access_token)
    if not access_token or not user_actual:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "view.html", {"username":user_actual})

@router.get("/profile")
def profile(current_user=Depends(get_current_user)):
    return current_user

#POST routes

@router.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    #hashed_pass = hash_password(user.password)
                                     
    new_user = User(
        username = username,
        email = email,
        password = password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse("login", status_code = 302)

@router.post("/login")
def login(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = verify_user_database(db, username, password)
    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "Username or password invalid"})
    
    token = create_access_token({"sub":user["username"], "user_id":user["id"]})
    response = RedirectResponse("view", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    
    return response
