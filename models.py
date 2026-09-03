from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Trader(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    whatsapp_number: str
    business_category: str
    store_slug: str = Field(unique=True, index=True)
    profile_photo_url: str
    bio: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    input_method: str


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trader_id: int = Field(foreign_key="trader.id")
    name: str
    price_inr: float
    description: Optional[str] = None
    photo_url: str
    whatsapp_order_message: str
    graphic_url: Optional[str] = None
    display_order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
