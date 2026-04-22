from __future__ import annotations

import asyncio


class MarketplaceService:
    def __init__(self):
        pass

    async def publish_variant(self, variant_id: int, marketplace: str) -> dict[str, str]:
        await asyncio.sleep(2)

        marketplace_urls = {
            "wildberries": f"https://www.wildberries.ru/catalog/{variant_id}/detail.aspx",
            "ozon": f"https://www.ozon.ru/product/{variant_id}",
            "amazon": f"https://www.amazon.com/dp/MOCK{variant_id}",
        }

        return {
            "success": True,
            "marketplace": marketplace,
            "listing_url": marketplace_urls.get(
                marketplace, f"https://{marketplace}.mock/listing/{variant_id}"
            ),
            "status": "published",
        }

    async def get_real_metrics(self, variant_id: int, marketplace: str) -> dict[str, int]:
        await asyncio.sleep(1)

        return {
            "variant_id": variant_id,
            "marketplace": marketplace,
            "views": 0,
            "clicks": 0,
            "conversions": 0,
            "status": "mock_data",
        }
