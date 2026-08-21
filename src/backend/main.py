import os
from dotenv import load_dotenv
from fastapi import FastAPI
from src.backend.routes.auth import auth_router

load_dotenv()
app = FastAPI()
app.include_router(auth_router)