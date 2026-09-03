import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Only use env DATABASE_URL if it looks like a valid SQLAlchemy connection string
if _DATABASE_URL and any(_DATABASE_URL.startswith(p) for p in ("sqlite:", "postgresql:", "mysql:", "sqlite://")):
    DATABASE_URL = _DATABASE_URL
else:
    DATABASE_URL = "sqlite:///trader_storefront.db"

# SQLite needs check_same_thread=False for FastAPI async usage
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
