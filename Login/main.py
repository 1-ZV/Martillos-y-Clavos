from fastapi import FastAPI
from Core.database import Base, engine
from .routes import router

Base.metadata.create_all(bind=engine)

app_login = FastAPI()

app_login.include_router(router)