from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Create Campaign"), KeyboardButton(text="My Campaigns")],
            [KeyboardButton(text="Account"), KeyboardButton(text="Plans")],
        ],
        resize_keyboard=True,
    )


def platform_selection_keyboard(selected: list[str] = None) -> InlineKeyboardMarkup:
    if selected is None:
        selected = []

    platforms = ["instagram", "tiktok", "amazon", "wildberries", "ozon"]
    buttons = []

    for platform in platforms:
        check = "✅ " if platform in selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{check}{platform.title()}",
                callback_data=f"platform_toggle:{platform}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🚀 Generate Campaign", callback_data="platform_confirm")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def campaign_list_keyboard(campaigns: list[dict]) -> InlineKeyboardMarkup:
    buttons = []

    for campaign in campaigns[:10]:
        status_emoji = {
            "pending": "⏳",
            "generating": "🔄",
            "ready": "✅",
            "testing": "🧪",
            "completed": "🏁",
            "failed": "❌",
        }.get(campaign["status"], "❓")

        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {campaign['product_name'][:30]}",
                callback_data=f"campaign_open:{campaign['id']}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def campaign_actions_keyboard(campaign_id: int, has_metrics: bool = False) -> InlineKeyboardMarkup:
    buttons = []

    if not has_metrics:
        buttons.append([
            InlineKeyboardButton(
                text="🧪 Start A/B Test",
                callback_data=f"start_test:{campaign_id}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📊 View Analytics",
                callback_data=f"view_analytics:{campaign_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Back", callback_data="back_to_campaigns")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def variant_actions_keyboard(variant_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📤 Publish to Marketplace",
                callback_data=f"publish_variant:{variant_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Back", callback_data="back_to_campaign")
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def marketplace_selection_keyboard(variant_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="Wildberries",
                callback_data=f"marketplace_publish:{variant_id}:wildberries"
            )
        ],
        [
            InlineKeyboardButton(
                text="Ozon",
                callback_data=f"marketplace_publish:{variant_id}:ozon"
            )
        ],
        [
            InlineKeyboardButton(
                text="Amazon",
                callback_data=f"marketplace_publish:{variant_id}:amazon"
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel_publish")
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def plans_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Pro - $49/мес", callback_data="sub:pro")
        ],
        [
            InlineKeyboardButton(text="Business - $199/мес", callback_data="sub:business")
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
