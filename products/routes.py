from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from .models import CartItem, Order, DetalleOrden, Cart, StatusEnum
from Core.database import get_db
from CRUD.models import Products
from .schemas import CartItemCreate, CartItemResponse, OrdenResponse, CrearOrden
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import stripe
from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder

router = APIRouter()
templates = Jinja2Templates(directory="templates")
USER_ID_SIMULADO = 1
stripe.api_key = "tu_sk_test_SECRET_KEY_DE_STRIPE"

@router.get("/", response_class=HTMLResponse)
def all_products(request: Request, db: Session = Depends(get_db)):
    list = db.query(Products).all()
    return templates.TemplateResponse(request, "all_products.html", {"products": list})

@router.get("/cart", response_class=HTMLResponse)
def get_cart(request: Request, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == USER_ID_SIMULADO).options(
        joinedload(Cart.items).joinedload(CartItem.product)
    ).first()
    
    items = cart.items if cart else []

    total = sum(item.product.price * item.amount for item in items if item.product)
    return templates.TemplateResponse(request,"cart.html", {"items": items, "total": round(total, 2)})

@router.post("/cart", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(item: CartItemCreate, db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    cart = db.query(Cart).filter(Cart.user_id == USER_ID_SIMULADO).first()
    if not cart:
        cart = Cart(user_id=USER_ID_SIMULADO)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item.product_id
    ).first()
    
    if cart_item:
        cart_item.amount += item.amount
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item.product_id,
            amount=item.amount
        )
        db.add(cart_item)
        
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.post("/cart_delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    # 1. Localizar el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == USER_ID_SIMULADO).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
        
    # 2. Borrar únicamente el ítem del producto seleccionado dentro de ese carrito
    db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).delete()
    
    db.commit()
    return JSONResponse({"success": True})


"""@router.post("/cart", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(item: CartItemCreate, db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == USER_ID_SIMULADO,
        CartItem.product_id == item.product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(
            user_id=USER_ID_SIMULADO,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(cart_item)
        
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.get("/cart", response_class=HTMLResponse)
def get_cart(request: Request,db: Session = Depends(get_db)):
    items = db.query(Cart).filter(Cart.user_id == USER_ID_SIMULADO).all()
    cart_items = (db.query(CartItem).options(joinedload(CartItem.product)).filter(Cart.user_id == USER_ID_SIMULADO).all())
    total = sum(item.product.price * item.quantity for item in items)
    
    return templates.TemplateResponse(request, "cart.html", {"items":items, "total":round(total, 2), "products":cart_items})

@router.post("/products/cart_delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db.query(Cart).filter(Cart.id == product_id).delete()
    db.commit()
    return JSONResponse({"success": True})"""


@router.post("/ordenes_crear", response_model=OrdenResponse)
def crear_orden_desde_carrito(payload: CrearOrden, db: Session = Depends(get_db)):
    # 1. Buscar el carrito del usuario con todos sus productos (Eager Loading)
    carrito = db.query(Cart).filter(Cart.user_id == payload.user_id).options(
        joinedload(Cart.items).joinedload(CartItem.product)
    ).first()

    # Validación: Si no hay carrito o está vacío, no se puede comprar
    if not carrito or not carrito.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El carrito está vacío o no existe."
        )

    # 2. Calcular el total acumulado de la orden congelando los precios actuales
    total_orden = 0.0
    detalles_orden_db = []

    for item in carrito.items:
        if not item.product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"El producto con ID {item.product_id} ya no existe en el inventario."
            )
        
        # Calcular subtotal de este producto usando su precio ACTUAL en la ferretería
        subtotal = item.amount * item.product.price
        total_orden += subtotal

        # Preparar el registro para la tabla intermedia 'order_items'
        nuevo_detalle = DetalleOrden(
            product_id=item.product_id,
            amount=item.amount,
            unit_price=item.product.price # ⚠️ AQUÍ CONGELAMOS EL PRECIO
        )
        detalles_orden_db.append(nuevo_detalle)

    try:
        # 3. Solicitar el PaymentIntent a Stripe (Stripe procesa en centavos enteros)
        monto_en_centavos = int(total_orden * 100)
        intento_pago = stripe.PaymentIntent.create(
            amount=monto_en_centavos,
            currency="usd", # O tu moneda local: "mxn", "cop", etc.
            metadata={"user_id": payload.user_id}
        )

        # 4. Crear la Orden Principal en MySQL
        nueva_orden = Order(
            user_id=payload.user_id,
            total=total_orden,
            stripe_payment_id=intento_pago.id, # Guardamos el ID de Stripe para el Webhook
            status=StatusEnum.PENDING,
            details=detalles_orden_db # SQLAlchemy asocia automáticamente los detalles_orden_db a esta orden
        )
        
        db.add(nueva_orden)

        # 5. ¡VACIAR EL CARRITO! 
        # Como ya migramos los productos a la orden, borramos los items del carrito
        for item in carrito.items:
            db.delete(item)

        # Confirmamos los cambios en la Base de Datos (Todo ocurre en una sola transacción)
        db.commit()
        db.refresh(nueva_orden)

        # 6. Responder al Frontend
        # Le enviamos los datos de la orden y el client_secret para que Stripe complete el pago en el cliente
        return {
            "id": nueva_orden.id,
            "user_id": nueva_orden.user_id,
            "amount": nueva_orden.total,
            "status": nueva_orden.status,
            "created_at": nueva_orden.created_at,
            "details": nueva_orden.details,
            "stripe_client_secret": intento_pago.client_secret # El frontend necesita esto
        }

    except stripe.error.StripeError as e:
        db.rollback() # Si Stripe falla, no tocamos la base de datos
        raise HTTPException(status_code=400, detail=f"Error con el proveedor de pagos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

    """try:
        nueva_orden = Order(user_id=payload.user_id, total=0.0)
        db.add(nueva_orden)
        db.commit()
        db.refresh(nueva_orden)
        
        total_acumulado = 0.0
        
        # 2. Recorrer los productos enviados (el carrito) y agregarlos a los detalles
        for item in payload.items:
            # Buscamos el producto en la BD para asegurarnos de que existe y verificar el precio real
            db_producto = db.query(Products).filter(Products.id == item.product_id).first()
            if not db_producto:
                raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado")
            
            subtotal = db_producto.price * item.amount
            total_acumulado += subtotal
            
            # Guardamos en la tabla intermedia
            nuevo_detalle = DetalleOrden(
                order_id=nueva_orden.id,
                product_id=item.product_id,
                amount=item.amount,
                unit_price=db_producto.price
            )
            db.add(nuevo_detalle)
        
        # 3. Actualizamos el total real de la orden en MySQL
        nueva_orden.total = total_acumulado
        db.commit()
        db.refresh(nueva_orden)
        
        # 4. Generamos el PaymentIntent de Stripe enviando la ÚNICA llave primaria (nueva_orden.id)
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total_acumulado * 100), # Stripe procesa en centavos (ej: $10.50 -> 1050)
                currency="usd",
                metadata={
                    "orden_id": nueva_orden.id # Aquí ligamos Stripe con tu MySQL
                }
            )
            
            # Nota: En una app real, deberías retornar también el `intent.client_secret` 
            # al frontend para que completen el pago. Aquí retornamos la orden según el schema.
            return nueva_orden

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error con Stripe: {str(e)}")
    except ValidationError as e:
        print(e.json()) # <--- Esto te dirá exactamente qué campo causó el 422
        return JSONResponse(status_code=422, content=jsonable_encoder(e.errors()))
    # 1. Crear la instancia de la Orden principal (con total 0 inicialmente)"""
    