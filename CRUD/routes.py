from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from Core.database import get_db
from .models import Products
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def get_products(request: Request, db: Session = Depends(get_db)):
    list_products = db.query(Products).all()
    return templates.TemplateResponse(request, "products.html", {"products": list_products})

@router.get("/add_products", response_class=HTMLResponse)
def add_product(request: Request):
    return templates.TemplateResponse(request, "add_products.html")

@router.get("/delete_products", response_class=HTMLResponse)
def add_product(request: Request):
    return templates.TemplateResponse(request, "delete_products.html")

@router.get("/edit_products", response_class=HTMLResponse)
def edit_product(request: Request):
    #list_products = get_products_database(db)
    return templates.TemplateResponse(request, "edit_products.html")

@router.get("/search_products", response_class=HTMLResponse)
def seaarch_product(request: Request):
    return templates.TemplateResponse(request, "search_products.html", {"products": None})

#POST Methods

@router.post("/add_products")
def add_product(name: str = Form(...), description: str = Form(...), price: float = Form(...), stock: int = Form(...), db: Session = Depends(get_db)):
    new_product = Products(
        name = name,
        description = description,
        price = price,
        stock = stock
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return RedirectResponse("./", status_code = 302)

@router.post("/edit_products")
def edit_product(product_id: int = Form(...) ,name: str = Form(...), description: str = Form(...), price: float = Form(...), stock: int = Form(...), db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.name = name
    product.description = description
    product.price = price
    product.stock = stock

    db.commit()
    return RedirectResponse(url="./", status_code=303)

@router.post("/delete_products")
def delete_product(product_id: int = Form(...), db: Session = Depends(get_db)):
    db.query(Products).filter(Products.id == product_id).delete()
    db.commit()
    return RedirectResponse("./", status_code = 302)

@router.post("/search_products", response_class=HTMLResponse)
def seaarch_product(request: Request, product_id: int = Form(...), db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.id == product_id).first()
    error_message = None
    if not product:
        error_message = f"No se encontró ningún producto con el ID {product_id}"
    
    return templates.TemplateResponse(request, "search_products.html", {"products":product, "message": error_message})

