import os
import httpx


N8N_WEBHOOK_URL = os.getenv("N8N_GRAPHIC_WEBHOOK_URL", "YOUR_N8N_GRAPHIC_WEBHOOK_URL")


async def trigger_graphic_generation(
    trader_whatsapp: str,
    product_name: str,
    price: str,
    product_photo_url: str,
    language: str,
):
    """Fire-and-forget: POST product data to n8n graphic generator webhook.
    Must NEVER be awaited directly — use asyncio.create_task() only.
    """
    payload = {
        "event": "store_product_added",
        "trader_whatsapp": trader_whatsapp,
        "product_name": product_name,
        "price": f"\u20b9{price}",
        "photo_url": product_photo_url,
        "language": language,
        "mode": "1",
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=5.0,
            )
        except Exception:
            pass
