import os
from dotenv import load_dotenv
from fastapi import FastAPI
from src.backend.routes import *

load_dotenv()
app = FastAPI(debug=os.getenv("DEBUG", "False").lower() == "true")
app.include_router(amenity_router)
app.include_router(property_amenity_router)
app.include_router(room_amenity_router)
app.include_router(auth_router)
app.include_router(booking_router)
app.include_router(favorites_router)
app.include_router(review_router)
app.include_router(review_property_router)
app.include_router(room_router)
app.include_router(user_router)
