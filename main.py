import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import create_db_and_tables
from routes.pages import router as pages_router
from routes.store import router as store_router

app = FastAPI(title="Trader Storefront Generator")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve locally uploaded images
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(store_router)
app.include_router(pages_router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    logging.getLogger("trader-storefront").info("Application started, database tables created/verified.")
