from fastapi import FastAPI, Request
from Login.main import app_login
from CRUD.routes import router as CRUD_router
from products.routes import router as products_router
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from Core.database import engine
from Core import base_models
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    base_models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.mount("/login", app_login)
app.include_router(CRUD_router, prefix="/CRUD")
app.include_router(products_router, prefix="/products")

@app.get("/", response_class=HTMLResponse)
def inicio_global(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/inicio")
def inicio_global():
    return RedirectResponse(url="/CRUD/")

@app.get("/login", response_class=HTMLResponse)
def inicio_global(request: Request):
    return templates.TemplateResponse(request, "login.html")

"""@app.get("/products", response_class=HTMLResponse)
def inicio_global(request: Request):
    return templates.TemplateResponse(request, "products.html")"""

@app.get("/products")
def all_products():
    return RedirectResponse(url="/products/")