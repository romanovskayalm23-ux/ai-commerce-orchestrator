from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Campaign:
    id: int
    user_id: int
    product_name: str
    product_photo_url: str
    status: str  # pending/generating/ready/testing/completed
    created_at: str
    updated_at: str


@dataclass
class Variant:
    id: int
    campaign_id: int
    platform: str
    visual_url: str
    copy_text: str
    hashtags: str
    description: str
    views: int
    clicks: int
    conversions: int
    ctr: float
    conversion_rate: float
    is_winner: bool
    created_at: str


@dataclass
class WinningPattern:
    id: int
    platform: str
    pattern_type: str
    pattern_data: str  # JSON string
    avg_ctr: float
    avg_conversion_rate: float
    usage_count: int
    created_at: str
