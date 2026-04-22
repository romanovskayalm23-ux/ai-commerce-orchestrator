from __future__ import annotations

import asyncio
import json
import random
from typing import Any

from database import Database


class ABTestingService:
    def __init__(self, db: Database):
        self.db = db

    async def simulate_metrics(self, variant_id: int, duration_hours: int = 24) -> dict[str, Any]:
        await asyncio.sleep(1)

        views = random.randint(1000, 10000)
        ctr = random.uniform(0.01, 0.15)
        cr = random.uniform(0.02, 0.10)
        clicks = int(views * ctr)
        conversions = int(clicks * cr)

        await self.db.update_variant_metrics(variant_id, views, clicks, conversions)

        return {
            "variant_id": variant_id,
            "views": views,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": round(ctr * 100, 2),
            "conversion_rate": round(cr * 100, 2),
        }

    async def simulate_campaign_test(self, campaign_id: int) -> list[dict[str, Any]]:
        variants = await self.db.get_campaign_variants(campaign_id)
        results = []

        for variant in variants:
            result = await self.simulate_metrics(variant["id"])
            results.append(result)

        return results

    async def analyze_campaign(self, campaign_id: int) -> dict[str, Any]:
        variants = await self.db.get_campaign_variants(campaign_id)

        if not variants:
            return {"error": "No variants found"}

        winner = max(
            variants,
            key=lambda v: (v["ctr"] / 100) * (v["conversion_rate"] / 100),
        )

        await self.db.mark_variant_as_winner(winner["id"])

        insights = self._generate_insights(variants, winner)

        return {
            "winner_id": winner["id"],
            "winner_platform": winner["platform"],
            "winner_ctr": winner["ctr"],
            "winner_cr": winner["conversion_rate"],
            "insights": insights,
        }

    def _generate_insights(
        self, variants: list[dict[str, Any]], winner: dict[str, Any]
    ) -> list[str]:
        insights = []

        avg_ctr = sum(v["ctr"] for v in variants) / len(variants)
        avg_cr = sum(v["conversion_rate"] for v in variants) / len(variants)

        insights.append(
            f"🏆 Победитель: {winner['platform'].title()} с CTR {winner['ctr']:.2f}% и CR {winner['conversion_rate']:.2f}%"
        )

        if winner["ctr"] > avg_ctr * 1.5:
            insights.append(
                f"📈 CTR победителя на {((winner['ctr'] / avg_ctr - 1) * 100):.0f}% выше среднего"
            )

        if winner["conversion_rate"] > avg_cr * 1.5:
            insights.append(
                f"💰 Конверсия победителя на {((winner['conversion_rate'] / avg_cr - 1) * 100):.0f}% выше среднего"
            )

        worst = min(variants, key=lambda v: v["ctr"])
        insights.append(
            f"⚠️ Худший результат: {worst['platform'].title()} с CTR {worst['ctr']:.2f}%"
        )

        total_conversions = sum(v["conversions"] for v in variants)
        insights.append(f"📊 Всего конверсий: {total_conversions}")

        return insights
