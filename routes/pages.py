import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from models import Trader, Product
from database import get_session

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/create-store", response_class=HTMLResponse)
async def create_store_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})


@router.get("/store/{slug}", response_class=HTMLResponse)
async def storefront_page(slug: str, request: Request):
    session = next(get_session())
    trader = session.exec(select(Trader).where(Trader.store_slug == slug, Trader.is_active == True)).first()
    if not trader:
        return templates.TemplateResponse(
            "store.html",
            {"request": request, "trader": None, "products": [], "not_found": True},
            status_code=404,
        )

    products = session.exec(
        select(Product)
        .where(Product.trader_id == trader.id)
        .order_by(Product.display_order)
    ).all()

    return templates.TemplateResponse(
        "store.html",
        {
            "request": request,
            "trader": trader,
            "products": products,
            "not_found": False,
        },
    )


@router.get("/store/{slug}/success", response_class=HTMLResponse)
async def success_page(slug: str, request: Request):
    session = next(get_session())
    trader = session.exec(select(Trader).where(Trader.store_slug == slug)).first()
    if not trader:
        return RedirectResponse("/")

    products = session.exec(
        select(Product).where(Product.trader_id == trader.id)
    ).all()

    store_url = f"{request.base_url}store/{trader.store_slug}"
    whatsapp_share_text = f"Check out my store: {store_url}"

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "trader": trader,
            "products": products,
            "store_url": store_url,
            "whatsapp_share_text": whatsapp_share_text,
        },
    )
