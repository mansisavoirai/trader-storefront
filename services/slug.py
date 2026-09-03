import re
from slugify import slugify
from sqlmodel import select
from models import Trader


def generate_slug(name: str, db) -> str:
    base = slugify(name)
    slug = base
    counter = 1
    while db.exec(select(Trader).where(Trader.store_slug == slug)).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug
