from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import Database
from keyboards import (
    campaign_actions_keyboard,
    campaign_list_keyboard,
    main_menu_keyboard,
    marketplace_selection_keyboard,
    platform_selection_keyboard,
    plans_keyboard,
)
from services.ab_testing import ABTestingService
from services.analytics import AnalyticsService
from services.generation import PLAN_LIMITS, PLAN_MAX_PLATFORMS, PLAN_PERIODS, PLAN_PRIORITIES
from services.marketplace import MarketplaceService
from services.queue import QueueService


class CampaignCreation(StatesGroup):
    waiting_product_name = State()
    waiting_product_photo = State()
    waiting_platform_selection = State()


def create_router(
    db: Database,
    queue_service: QueueService,
    ab_testing: ABTestingService,
    analytics: AnalyticsService,
    marketplace: MarketplaceService,
) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        await state.clear()
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username or "")

        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "🚀 AI Commerce Orchestrator - платформа для создания продуктовых кампаний с A/B тестированием.\n\n"
            "Что я умею:\n"
            "• Генерировать варианты для разных платформ (Instagram, TikTok, Amazon, Wildberries, Ozon)\n"
            "• Запускать A/B тесты и анализировать метрики\n"
            "• Самообучаться на основе лучших результатов\n"
            "• Публиковать на маркетплейсы\n\n"
            f"Твой тариф: {user['plan']}\n"
            "Используй меню ниже для начала работы.",
            reply_markup=main_menu_keyboard(),
        )

    @router.message(F.text == "Create Campaign")
    @router.message(Command("create_campaign"))
    async def cmd_create_campaign(message: Message, state: FSMContext) -> None:
        user = await db.get_or_create_user(message.from_user.id)

        plan = user.get("plan", "free")
        limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        period = PLAN_PERIODS.get(plan, "daily")
        used = user.get("daily_used", 0) if period == "daily" else user.get("monthly_used", 0)

        if used >= limit:
            await message.answer(
                f"❌ Лимит кампаний исчерпан ({used}/{limit} за {period}).\n\n"
                "Апгрейдни тариф командой /plans",
                reply_markup=plans_keyboard(),
            )
            return

        await state.set_state(CampaignCreation.waiting_product_name)
        await message.answer(
            "📝 Создание новой кампании\n\n"
            "Шаг 1/3: Введи название товара (например: 'Wireless Headphones')"
        )

    @router.message(CampaignCreation.waiting_product_name)
    async def handle_product_name(message: Message, state: FSMContext) -> None:
        product_name = message.text.strip()

        if len(product_name) < 3:
            await message.answer("❌ Название слишком короткое. Введи минимум 3 символа.")
            return

        await state.update_data(product_name=product_name)
        await state.set_state(CampaignCreation.waiting_product_photo)

        await message.answer(
            f"✅ Товар: {product_name}\n\n"
            "Шаг 2/3: Загрузи фото товара"
        )

    @router.message(CampaignCreation.waiting_product_photo, F.photo)
    async def handle_product_photo(message: Message, state: FSMContext) -> None:
        photo = message.photo[-1]
        photo_url = f"https://api.telegram.org/file/bot<token>/{photo.file_id}"

        await state.update_data(product_photo_url=photo_url)
        await state.set_state(CampaignCreation.waiting_platform_selection)

        user = await db.get_or_create_user(message.from_user.id)
        plan = user.get("plan", "free")
        max_platforms = PLAN_MAX_PLATFORMS.get(plan, 3)

        await message.answer(
            f"✅ Фото загружено\n\n"
            f"Шаг 3/3: Выбери платформы (макс {max_platforms} для тарифа {plan})",
            reply_markup=platform_selection_keyboard([]),
        )

    @router.callback_query(F.data.startswith("platform_toggle:"))
    async def callback_platform_toggle(callback: CallbackQuery, state: FSMContext) -> None:
        platform = callback.data.split(":")[1]
        data = await state.get_data()
        selected = data.get("selected_platforms", [])

        user = await db.get_or_create_user(callback.from_user.id)
        plan = user.get("plan", "free")
        max_platforms = PLAN_MAX_PLATFORMS.get(plan, 3)

        if platform in selected:
            selected.remove(platform)
        else:
            if len(selected) >= max_platforms:
                await callback.answer(f"❌ Максимум {max_platforms} платформ для тарифа {plan}", show_alert=True)
                return
            selected.append(platform)

        await state.update_data(selected_platforms=selected)
        await callback.message.edit_reply_markup(reply_markup=platform_selection_keyboard(selected))
        await callback.answer()

    @router.callback_query(F.data == "platform_confirm")
    async def callback_platform_confirm(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        selected = data.get("selected_platforms", [])

        if not selected:
            await callback.answer("❌ Выбери хотя бы одну платформу", show_alert=True)
            return

        product_name = data.get("product_name")
        product_photo_url = data.get("product_photo_url")

        campaign_id = await db.create_campaign(
            user_id=callback.from_user.id,
            product_name=product_name,
            product_photo_url=product_photo_url,
        )

        user = await db.get_or_create_user(callback.from_user.id)
        plan = user.get("plan", "free")
        priority = PLAN_PRIORITIES.get(plan, 20)
        period = PLAN_PERIODS.get(plan, "daily")

        if period == "daily":
            await db.increment_daily_used(callback.from_user.id)
        else:
            await db.increment_monthly_used(callback.from_user.id)

        task_id = await queue_service.enqueue(
            user_id=callback.from_user.id,
            campaign_id=campaign_id,
            product_name=product_name,
            platforms=selected,
            priority=priority,
        )

        await state.clear()

        await callback.message.edit_text(
            f"✅ Кампания #{campaign_id} создана!\n\n"
            f"Товар: {product_name}\n"
            f"Платформы: {', '.join(p.title() for p in selected)}\n"
            f"Задача #{task_id} в очереди (приоритет: {priority})\n\n"
            f"⏳ Генерация займет ~{len(selected) * 3} секунд. Я пришлю уведомление когда будет готово."
        )
        await callback.answer()

    @router.message(F.text == "My Campaigns")
    @router.message(Command("campaigns"))
    async def cmd_campaigns(message: Message) -> None:
        campaigns = await db.get_user_campaigns(message.from_user.id, limit=10)

        if not campaigns:
            await message.answer(
                "📭 У тебя пока нет кампаний.\n\n"
                "Создай первую с помощью /create_campaign"
            )
            return

        await message.answer(
            f"📊 Твои кампании ({len(campaigns)}):",
            reply_markup=campaign_list_keyboard(campaigns),
        )

    @router.callback_query(F.data.startswith("campaign_open:"))
    async def callback_campaign_open(callback: CallbackQuery) -> None:
        campaign_id = int(callback.data.split(":")[1])
        campaign = await db.get_campaign(campaign_id)

        if not campaign:
            await callback.answer("❌ Кампания не найдена", show_alert=True)
            return

        variants = await db.get_campaign_variants(campaign_id)
        has_metrics = any(v["views"] > 0 for v in variants)

        text = f"📊 Кампания #{campaign_id}\n\n"
        text += f"Товар: {campaign['product_name']}\n"
        text += f"Статус: {campaign['status']}\n"
        text += f"Вариантов: {len(variants)}\n\n"

        if variants:
            text += "Варианты:\n"
            for v in variants:
                winner = "🏆 " if v["is_winner"] else ""
                text += f"\n{winner}{v['platform'].title()}\n"
                if v["views"] > 0:
                    text += f"  Views: {v['views']} | CTR: {v['ctr']:.2f}% | CR: {v['conversion_rate']:.2f}%\n"
                text += f"  {v['copy_text'][:50]}...\n"

        await callback.message.edit_text(
            text,
            reply_markup=campaign_actions_keyboard(campaign_id, has_metrics),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("start_test:"))
    async def callback_start_test(callback: CallbackQuery) -> None:
        campaign_id = int(callback.data.split(":")[1])

        await callback.message.edit_text("🧪 Запускаю A/B тест...\n\nСимулирую метрики для всех вариантов...")
        await callback.answer()

        results = await ab_testing.simulate_campaign_test(campaign_id)
        analysis = await ab_testing.analyze_campaign(campaign_id)

        await db.update_campaign_status(campaign_id, "testing")

        text = f"✅ A/B тест завершен!\n\n"
        text += "\n".join(analysis["insights"])

        await callback.message.edit_text(text, reply_markup=campaign_actions_keyboard(campaign_id, True))

    @router.callback_query(F.data.startswith("view_analytics:"))
    async def callback_view_analytics(callback: CallbackQuery) -> None:
        campaign_id = int(callback.data.split(":")[1])

        roi_data = await analytics.calculate_roi(campaign_id)
        pattern_id = await analytics.extract_winning_patterns(campaign_id)

        text = f"📈 Аналитика кампании #{campaign_id}\n\n"
        text += f"👁 Просмотры: {roi_data['total_views']}\n"
        text += f"👆 Клики: {roi_data['total_clicks']}\n"
        text += f"💰 Конверсии: {roi_data['total_conversions']}\n\n"
        text += f"📊 Средний CTR: {roi_data['avg_ctr']}%\n"
        text += f"📊 Средний CR: {roi_data['avg_cr']}%\n\n"
        text += f"💵 Выручка: {roi_data['total_revenue']} ₽\n"
        text += f"💸 Затраты: {roi_data['campaign_cost']} ₽\n"
        text += f"📈 ROI: {roi_data['roi']}%\n\n"

        if pattern_id:
            text += f"🧠 Паттерн победителя сохранен (ID: {pattern_id})\n"
            text += "Будет использован для улучшения следующих кампаний!"

        await callback.message.edit_text(text, reply_markup=campaign_actions_keyboard(campaign_id, True))
        await callback.answer()

    @router.callback_query(F.data.startswith("publish_variant:"))
    async def callback_publish_variant(callback: CallbackQuery) -> None:
        variant_id = int(callback.data.split(":")[1])

        await callback.message.edit_text(
            f"📤 Публикация варианта #{variant_id}\n\nВыбери маркетплейс:",
            reply_markup=marketplace_selection_keyboard(variant_id),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("marketplace_publish:"))
    async def callback_marketplace_publish(callback: CallbackQuery) -> None:
        parts = callback.data.split(":")
        variant_id = int(parts[1])
        marketplace_name = parts[2]

        await callback.message.edit_text(f"⏳ Публикую на {marketplace_name.title()}...")
        await callback.answer()

        result = await marketplace.publish_variant(variant_id, marketplace_name)

        text = f"✅ Опубликовано на {marketplace_name.title()}!\n\n"
        text += f"🔗 URL: {result['listing_url']}\n"
        text += f"Статус: {result['status']}"

        await callback.message.edit_text(text)

    @router.message(F.text == "Account")
    @router.message(Command("account"))
    async def cmd_account(message: Message) -> None:
        user = await db.get_or_create_user(message.from_user.id)

        plan = user.get("plan", "free")
        limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        period = PLAN_PERIODS.get(plan, "daily")
        used = user.get("daily_used", 0) if period == "daily" else user.get("monthly_used", 0)

        text = f"👤 Твой аккаунт\n\n"
        text += f"Тариф: {plan.title()}\n"
        text += f"Использовано: {used}/{limit} кампаний за {period}\n"

        await message.answer(text)

    @router.message(F.text == "Plans")
    @router.message(Command("plans"))
    async def cmd_plans(message: Message) -> None:
        text = "💎 Тарифные планы\n\n"
        text += "🆓 Free:\n"
        text += "  • 2 кампании/день\n"
        text += "  • 3 платформы макс\n"
        text += "  • Базовая аналитика\n\n"
        text += "⭐ Pro ($49/мес):\n"
        text += "  • 50 кампаний/месяц\n"
        text += "  • Все платформы\n"
        text += "  • Продвинутая аналитика\n"
        text += "  • A/B тесты\n\n"
        text += "🚀 Business ($199/мес):\n"
        text += "  • Безлимит кампаний\n"
        text += "  • Приоритетная генерация\n"
        text += "  • Self-learning\n"
        text += "  • API доступ\n"
        text += "  • Интеграция с маркетплейсами"

        await message.answer(text, reply_markup=plans_keyboard())

    @router.callback_query(F.data.startswith("sub:"))
    async def callback_subscribe(callback: CallbackQuery) -> None:
        plan = callback.data.split(":")[1]

        await db.conn.execute(
            "UPDATE users SET plan = ? WHERE user_id = ?",
            (plan, callback.from_user.id),
        )
        await db.conn.commit()

        await callback.message.edit_text(
            f"✅ Тариф изменен на {plan.title()}!\n\n"
            "Это mock-подписка. В продакшене здесь будет реальная оплата."
        )
        await callback.answer()

    @router.callback_query(F.data == "back_to_campaigns")
    async def callback_back_to_campaigns(callback: CallbackQuery) -> None:
        campaigns = await db.get_user_campaigns(callback.from_user.id, limit=10)
        await callback.message.edit_text(
            f"📊 Твои кампании ({len(campaigns)}):",
            reply_markup=campaign_list_keyboard(campaigns),
        )
        await callback.answer()

    return router
