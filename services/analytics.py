from __future__ import annotations

import json
from typing import Any

from database import Database


class AnalyticsService:
    def __init__(self, db: Database):
        self.db = db

    async def extract_winning_patterns(self, campaign_id: int) -> int | None:
        winner = await self.db.get_winner_variant(campaign_id)

        if not winner:
            return None

        pattern = {
            "visual_style": self._analyze_visual(winner["visual_url"]),
            "copy_tone": self._analyze_copy(winner["copy_text"]),
            "hashtag_set": winner["hashtags"].split()[:5],
        }

        pattern_id = await self.db.save_winning_pattern(
            platform=winner["platform"],
            pattern_type="combined",
            pattern_data=pattern,
            avg_ctr=winner["ctr"],
            avg_conversion_rate=winner["conversion_rate"],
        )

        return pattern_id

    def _analyze_visual(self, visual_url: str) -> str:
        styles = ["bright", "minimal", "dynamic", "clean", "infographic"]
        return styles[hash(visual_url) % len(styles)]

    def _analyze_copy(self, copy_text: str) -> str:
        if "🔥" in copy_text or "✨" in copy_text:
            return "energetic"
        elif "Премиум" in copy_text or "качество" in copy_text:
            return "premium"
        elif "Закажи" in copy_text or "Не упусти" in copy_text:
            return "urgent"
        else:
            return "informative"

    async def calculate_roi(self, campaign_id: int) -> dict[str, Any]:
        variants = await self.db.get_campaign_variants(campaign_id)

        if not variants:
            return {"error": "No variants found"}

        total_views = sum(v["views"] for v in variants)
        total_clicks = sum(v["clicks"] for v in variants)
        total_conversions = sum(v["conversions"] for v in variants)

        avg_ctr = (total_clicks / total_views * 100) if total_views > 0 else 0
        avg_cr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

        mock_revenue_per_conversion = 500
        mock_campaign_cost = 1000

        total_revenue = total_conversions * mock_revenue_per_conversion
        roi = ((total_revenue - mock_campaign_cost) / mock_campaign_cost * 100) if mock_campaign_cost > 0 else 0

        return {
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "avg_ctr": round(avg_ctr, 2),
            "avg_cr": round(avg_cr, 2),
            "total_revenue": total_revenue,
            "campaign_cost": mock_campaign_cost,
            "roi": round(roi, 2),
        }
