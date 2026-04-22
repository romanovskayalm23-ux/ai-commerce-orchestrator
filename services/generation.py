from __future__ import annotations

import asyncio
import json
import random
from typing import Any

from database import Database


PLAN_LIMITS = {
    "free": 2,
    "pro": 50,
    "business": 999999,
}

PLAN_PERIODS = {
    "free": "daily",
    "pro": "monthly",
    "business": "monthly",
}

PLAN_PRIORITIES = {
    "free": 20,
    "pro": 8,
    "business": 4,
}

PLAN_MAX_PLATFORMS = {
    "free": 3,
    "pro": 5,
    "business": 5,
}

PLATFORM_SPECS = {
    "instagram": {
        "aspect": "1:1",
        "style": "bright",
        "copy_length": "short",
        "emoji": True,
    },
    "tiktok": {
        "aspect": "9:16",
        "style": "dynamic",
        "copy_length": "medium",
        "emoji": True,
    },
    "amazon": {
        "aspect": "16:9",
        "style": "clean",
        "copy_length": "long",
        "emoji": False,
    },
    "wildberries": {
        "aspect": "1:1",
        "style": "minimal",
        "copy_length": "short",
        "emoji": False,
    },
    "ozon": {
        "aspect": "1:1",
        "style": "infographic",
        "copy_length": "medium",
        "emoji": False,
    },
}


class MultiPlatformGenerator:
    def __init__(self, db: Database):
        self.db = db

    async def generate_campaign(
        self,
        campaign_id: int,
        product_name: str,
        platforms: list[str],
    ) -> list[int]:
        variant_ids = []

        for platform in platforms:
            await asyncio.sleep(3)

            patterns = await self.db.get_best_patterns(platform, limit=3)
            variant_data = self._generate_variant(product_name, platform, patterns)

            variant_id = await self.db.create_variant(
                campaign_id=campaign_id,
                platform=platform,
                visual_url=variant_data["visual_url"],
                copy_text=variant_data["copy_text"],
                hashtags=variant_data["hashtags"],
                description=variant_data["description"],
            )

            variant_ids.append(variant_id)

            for pattern in patterns:
                await self.db.increment_pattern_usage(pattern["id"])

        return variant_ids

    def _generate_variant(
        self, product_name: str, platform: str, patterns: list[dict[str, Any]]
    ) -> dict[str, str]:
        spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])

        copy_templates = {
            "short": [
                f"✨ {product_name} - твой новый must-have!",
                f"🔥 {product_name} уже в наличии!",
                f"💎 Открой для себя {product_name}",
            ],
            "medium": [
                f"Представляем {product_name} - идеальное решение для тех, кто ценит качество и стиль. Закажи сейчас!",
                f"{product_name} - это то, что ты искал! Премиум качество по доступной цене. Не упусти шанс!",
                f"Почувствуй разницу с {product_name}. Инновационный дизайн и функциональность в одном продукте.",
            ],
            "long": [
                f"Описание товара: {product_name}\n\nПремиум качество, проверенное временем. Этот продукт создан для тех, кто не идет на компромиссы. Особенности: высокое качество материалов, современный дизайн, долговечность.\n\nЗакажите сейчас и получите быструю доставку!",
                f"{product_name} - ваш надежный выбор\n\nХарактеристики:\n- Высокое качество\n- Современный дизайн\n- Доступная цена\n- Быстрая доставка\n\nИдеально подходит для повседневного использования. Закажите прямо сейчас!",
            ],
        }

        hashtag_sets = {
            "instagram": "#shopping #style #musthave #новинки #покупки",
            "tiktok": "#tiktokmademebuyit #shopping #viral #fyp #новинки",
            "amazon": "#deals #shopping #quality #bestseller",
            "wildberries": "#wildberries #покупки #новинки #скидки #шоппинг",
            "ozon": "#ozon #покупки #доставка #качество #выгодно",
        }

        copy_length = spec["copy_length"]
        copy_text = random.choice(copy_templates.get(copy_length, copy_templates["short"]))

        if patterns:
            pattern_data = json.loads(patterns[0]["pattern_data"])
            if "copy_tone" in pattern_data:
                copy_text = f"{copy_text} {pattern_data['copy_tone']}"

        hashtags = hashtag_sets.get(platform, hashtag_sets["instagram"])

        description = f"Товар: {product_name}\nПлатформа: {platform.title()}\nФормат: {spec['aspect']}\nСтиль: {spec['style']}"

        visual_url = f"https://mock-cdn.example.com/{platform}/{random.randint(1000, 9999)}.jpg"

        return {
            "visual_url": visual_url,
            "copy_text": copy_text,
            "hashtags": hashtags,
            "description": description,
        }
