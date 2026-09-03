import os
import asyncio
import logging
from urllib.parse import quote
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import select
from pydantic import BaseModel
from typing import Optional, List

from models import Trader, Product
from services.cloudinary import upload_image
from services.slug import generate_slug
from services.graphic_trigger import trigger_graphic_generation

router = APIRouter(prefix="/api/store")
logger = logging.getLogger("trader-storefront")


def _build_order_url(trader_number: str, trader_name: str, product_name: str, price: float) -> str:
    message = (
        f"Hi {trader_name}! I saw your store and I'm interested in "
        f"{product_name} (\u20b9{price:.0f}). "
        f"Is it available? Please let me know."
    )
    return f"https://wa.me/91{trader_number}?text={quote(message)}"


def _get_session():
    from database import get_session
    return next(get_session())


# ---------- schemas ----------

class WhatsAppProduct(BaseModel):
    name: str
    price_inr: float
    description: Optional[str] = None
    photo_url: str
    language: str = "English"


class WhatsAppStoreCreate(BaseModel):
    name: str
    whatsapp_number: str
    business_category: str
    profile_photo_url: str
    bio: Optional[str] = None
    products: List[WhatsAppProduct]
    language: str = "English"


class TraderUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp_number: Optional[str] = None
    business_category: Optional[str] = None
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None


# ---------- endpoint 1: web form store creation ----------

@router.post("/create")
async def create_store_web(
    request: Request,
    trader_name: str = Form(...),
    whatsapp_number: str = Form(...),
    business_category: str = Form(...),
    profile_photo: UploadFile = File(...),
    slug_override: str = Form(default=""),
    bio: str = Form(default=""),
    # product fields (up to 10 sets)
    product_names: List[str] = Form(default=[]),
    product_prices: List[str] = Form(default=[]),
    product_descriptions: List[str] = Form(default=[]),
    product_photos: List[UploadFile] = File(default=[]),
):
    try:
        session = _get_session()

        # --- Validate inputs ---
        if not trader_name or not trader_name.strip():
            logger.warning("Create store failed: missing trader_name")
            return JSONResponse(status_code=422, content={"detail": "Business name is required."})

        clean_number = whatsapp_number.strip().replace("+", "").replace(" ", "")
        if not clean_number.isdigit() or len(clean_number) != 10:
            logger.warning(f"Create store failed: invalid whatsapp_number={whatsapp_number!r}")
            return JSONResponse(status_code=422, content={"detail": "WhatsApp number must be exactly 10 digits."})

        if not business_category or not business_category.strip():
            logger.warning("Create store failed: missing business_category")
            return JSONResponse(status_code=422, content={"detail": "Business category is required."})

        # Validate at least one product with name, price, and photo
        if not product_names or len(product_names) == 0:
            logger.warning("Create store failed: no products provided")
            return JSONResponse(status_code=422, content={"detail": "At least one product is required."})

        has_valid_product = False
        for i, pname in enumerate(product_names):
            if not pname.strip():
                continue
            if i < len(product_prices):
                try:
                    float(product_prices[i])
                except (ValueError, TypeError):
                    continue
                has_valid_product = True
                break

        if not has_valid_product:
            logger.warning("Create store failed: no valid product with name and price")
            return JSONResponse(status_code=422, content={"detail": "At least one product with a valid name and price is required."})

        # --- Upload profile photo ---
        try:
            profile_bytes = await profile_photo.read()
            if len(profile_bytes) == 0:
                logger.warning("Create store failed: empty profile photo")
                return JSONResponse(status_code=422, content={"detail": "Profile photo is required."})
            profile_url = upload_image(profile_bytes, folder="trader-storefront/profiles")
            logger.info(f"Profile photo uploaded: {profile_url}")
        except Exception as e:
            logger.error(f"Profile photo upload failed: {e}", exc_info=True)
            return JSONResponse(status_code=502, content={"detail": "Failed to upload profile photo. Please try again with a smaller image."})

        # --- Generate slug ---
        slug = slug_override.strip() if slug_override.strip() else generate_slug(trader_name, session)
        existing = session.exec(select(Trader).where(Trader.store_slug == slug)).first()
        if existing:
            slug = generate_slug(trader_name, session)

        # --- Create trader ---
        try:
            trader = Trader(
                name=trader_name.strip(),
                whatsapp_number=clean_number,
                business_category=business_category.strip(),
                store_slug=slug,
                profile_photo_url=profile_url,
                bio=bio.strip() or None,
                input_method="web",
            )
            session.add(trader)
            session.commit()
            session.refresh(trader)
            logger.info(f"Trader created: id={trader.id}, slug={slug}, name={trader_name!r}")
        except Exception as e:
            logger.error(f"Database error creating trader: {e}", exc_info=True)
            session.rollback()
            return JSONResponse(status_code=500, content={"detail": "Failed to save trader details. Please try again."})

        # --- Create products ---
        products_created = []
        for i, pname in enumerate(product_names):
            if not pname.strip():
                continue
            try:
                price_val = float(product_prices[i])
            except (ValueError, IndexError, TypeError):
                logger.warning(f"Skipping product {i}: invalid price")
                continue

            desc = product_descriptions[i].strip() if i < len(product_descriptions) else None
            if not desc:
                desc = None

            # Upload product photo
            photo_url = ""
            if i < len(product_photos) and product_photos[i] and product_photos[i].size > 0:
                try:
                    photo_bytes = await product_photos[i].read()
                    photo_url = upload_image(photo_bytes, folder=f"trader-storefront/products/{trader.id}")
                    logger.info(f"Product photo uploaded: {photo_url}")
                except Exception as e:
                    logger.error(f"Product photo upload failed for {pname!r}: {e}", exc_info=True)
                    return JSONResponse(
                        status_code=502,
                        content={"detail": f"Failed to upload photo for product: {pname.strip()}. Please try again."}
                    )
            else:
                logger.warning(f"Missing photo for product: {pname.strip()}")
                return JSONResponse(
                    status_code=422,
                    content={"detail": f"Photo is required for product: {pname.strip()}"}
                )

            order_url = _build_order_url(clean_number, trader_name, pname.strip(), price_val)

            try:
                product = Product(
                    trader_id=trader.id,
                    name=pname.strip(),
                    price_inr=price_val,
                    description=desc,
                    photo_url=photo_url,
                    whatsapp_order_message=order_url,
                    display_order=i,
                )
                session.add(product)
                session.commit()
                session.refresh(product)
                products_created.append(product)
                logger.info(f"Product created: id={product.id}, name={pname.strip()!r}")
            except Exception as e:
                logger.error(f"Database error creating product {pname!r}: {e}", exc_info=True)
                session.rollback()
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"Failed to save product: {pname.strip()}. Please try again."}
                )

            # fire-and-forget graphic trigger
            asyncio.create_task(
                trigger_graphic_generation(
                    trader_whatsapp=clean_number,
                    product_name=pname.strip(),
                    price=str(price_val),
                    product_photo_url=photo_url,
                    language="English",
                )
            )

        if not products_created:
            logger.warning(f"No products were created for trader {trader.id}")
            # Clean up trader if no products
            try:
                session.delete(trader)
                session.commit()
            except Exception:
                session.rollback()
            return JSONResponse(status_code=422, content={"detail": "No valid products were created. Please check your product details and try again."})

        store_url = f"{request.base_url}store/{trader.store_slug}"
        logger.info(f"Store created successfully: {store_url} with {len(products_created)} products")
        return {
            "store_url": store_url,
            "store_slug": trader.store_slug,
            "trader_id": trader.id,
        }

    except Exception as e:
        logger.error(f"Unexpected error in create_store_web: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again."})


# ---------- endpoint 2: WhatsApp/n8n store creation ----------

@router.post("/create-whatsapp")
async def create_store_whatsapp(request: Request, body: WhatsAppStoreCreate):
    try:
        session = _get_session()

        clean_number = body.whatsapp_number.strip().replace("+", "").replace(" ", "")

        slug = generate_slug(body.name, session)

        trader = Trader(
            name=body.name.strip(),
            whatsapp_number=clean_number,
            business_category=body.business_category.strip(),
            store_slug=slug,
            profile_photo_url=body.profile_photo_url,
            bio=body.bio,
            input_method="whatsapp",
        )
        session.add(trader)
        session.commit()
        session.refresh(trader)

        for i, p in enumerate(body.products):
            order_url = _build_order_url(clean_number, body.name, p.name, p.price_inr)
            product = Product(
                trader_id=trader.id,
                name=p.name,
                price_inr=p.price_inr,
                description=p.description,
                photo_url=p.photo_url,
                whatsapp_order_message=order_url,
                display_order=i,
            )
            session.add(product)
            session.commit()
            session.refresh(product)

            asyncio.create_task(
                trigger_graphic_generation(
                    trader_whatsapp=clean_number,
                    product_name=p.name,
                    price=str(p.price_inr),
                    product_photo_url=p.photo_url,
                    language=p.language,
                )
            )

        store_url = f"{request.base_url}store/{trader.store_slug}"
        return {
            "store_url": store_url,
            "store_slug": trader.store_slug,
            "trader_id": trader.id,
        }

    except Exception as e:
        logger.error(f"Error in create_store_whatsapp: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Failed to create store via WhatsApp."})


# ---------- endpoint 4: JSON store data ----------

@router.get("/{slug}")
async def get_store_json(slug: str, request: Request):
    try:
        session = _get_session()
        trader = session.exec(select(Trader).where(Trader.store_slug == slug)).first()
        if not trader or not trader.is_active:
            raise HTTPException(status_code=404, detail="Store not found.")

        products = session.exec(
            select(Product)
            .where(Product.trader_id == trader.id)
            .order_by(Product.display_order)
        ).all()

        return {
            "trader": trader.model_dump(),
            "products": [p.model_dump() for p in products],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching store {slug}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Failed to load store data."})


# ---------- endpoint 5: add single product ----------

@router.post("/{slug}/add-product")
async def add_product(
    slug: str,
    request: Request,
    product_name: str = Form(...),
    price: str = Form(...),
    description: str = Form(default=""),
    language: str = Form(default="English"),
    photo: UploadFile = File(...),
):
    try:
        session = _get_session()
        trader = session.exec(select(Trader).where(Trader.store_slug == slug)).first()
        if not trader:
            raise HTTPException(status_code=404, detail="Store not found.")

        photo_bytes = await photo.read()
        photo_url = upload_image(photo_bytes, folder=f"trader-storefront/products/{trader.id}")

        price_val = float(price)
        order_url = _build_order_url(trader.whatsapp_number, trader.name, product_name.strip(), price_val)

        existing_products = session.exec(
            select(Product).where(Product.trader_id == trader.id)
        ).all()
        next_order = max([p.display_order for p in existing_products], default=-1) + 1

        product = Product(
            trader_id=trader.id,
            name=product_name.strip(),
            price_inr=price_val,
            description=description.strip() or None,
            photo_url=photo_url,
            whatsapp_order_message=order_url,
            display_order=next_order,
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        asyncio.create_task(
            trigger_graphic_generation(
                trader_whatsapp=trader.whatsapp_number,
                product_name=product_name.strip(),
                price=str(price_val),
                product_photo_url=photo_url,
                language=language,
            )
        )

        return {
            "product_id": product.id,
            "whatsapp_order_message": product.whatsapp_order_message,
            "graphic_triggered": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding product to {slug}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Failed to add product."})


# ---------- endpoint 6: update trader ----------

@router.put("/{slug}/update")
async def update_store(slug: str, request: Request, body: TraderUpdate):
    try:
        session = _get_session()
        trader = session.exec(select(Trader).where(Trader.store_slug == slug)).first()
        if not trader:
            raise HTTPException(status_code=404, detail="Store not found.")

        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(trader, key, value)

        session.add(trader)
        session.commit()
        session.refresh(trader)

        return {"status": "updated", "trader": trader.model_dump()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating store {slug}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Failed to update store."})
