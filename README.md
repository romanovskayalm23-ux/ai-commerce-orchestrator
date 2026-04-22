# AI Commerce Orchestrator

AI-powered platform for creating multi-platform product campaigns with A/B testing and self-learning capabilities.

## Overview

AI Commerce Orchestrator generates product marketing campaigns across multiple platforms (Instagram, TikTok, Amazon, Wildberries, Ozon), runs A/B tests to identify winning variants, and learns from successful patterns to improve future campaigns.

## Features

### MVP Features
- **Multi-platform generation**: Create variants optimized for Instagram, TikTok, Amazon, Wildberries, and Ozon
- **A/B Testing**: Simulate metrics (views, clicks, conversions) and identify winning variants
- **Self-learning**: Extract patterns from winners and apply them to future campaigns
- **Marketplace integration**: Mock publishing to major marketplaces (ready for production APIs)
- **Tiered subscriptions**: Free, Pro, and Business plans with different limits
- **Priority queue**: Paid users get faster generation
- **Analytics & ROI**: Track campaign performance and calculate return on investment

## Architecture

```
ai-commerce-orchestrator/
├── bot.py                  # Bot initialization and lifecycle
├── config.py               # Configuration and environment variables
├── database.py             # SQLite database layer
├── handlers.py             # Telegram bot handlers and FSM
├── keyboards.py            # Inline and reply keyboards
├── main.py                 # Entry point
├── models/
│   └── schemas.py          # Data models (Campaign, Variant, WinningPattern)
└── services/
    ├── generation.py       # Multi-platform content generation
    ├── queue.py            # Priority queue for campaign generation
    ├── ab_testing.py       # A/B test simulation and analysis
    ├── analytics.py        # Pattern extraction and ROI calculation
    └── marketplace.py      # Marketplace publishing (mock)
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/romanovskayalm23-ux/ai-commerce-orchestrator.git
cd ai-commerce-orchestrator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
DB_PATH=commerce_orchestrator.db
LOG_LEVEL=info
OPENAI_API_KEY=optional_for_future_integration
```

4. Run the bot:
```bash
python main.py
```

## Usage

### Creating a Campaign

1. Start the bot: `/start`
2. Click "Create Campaign" or use `/create_campaign`
3. Enter product name (e.g., "Wireless Headphones")
4. Upload product photo
5. Select target platforms (up to 3 for free plan)
6. Wait for generation (~3 seconds per platform)

### Running A/B Tests

1. Go to "My Campaigns" or use `/campaigns`
2. Select a campaign
3. Click "Start A/B Test"
4. View simulated metrics (views, clicks, conversions, CTR, CR)
5. System automatically identifies the winner

### Viewing Analytics

1. After A/B test completes, click "View Analytics"
2. See total metrics, average CTR/CR, and ROI
3. Winning patterns are automatically extracted and saved
4. Future campaigns will use these patterns for better results

### Publishing to Marketplaces

1. Select a winning variant
2. Click "Publish to Marketplace"
3. Choose marketplace (Wildberries, Ozon, Amazon)
4. Get mock listing URL (ready for production API integration)

## Subscription Plans

### Free
- 2 campaigns/day
- 3 platforms max
- Basic analytics
- Watermark on visuals

### Pro ($49/month)
- 50 campaigns/month
- All 5 platforms
- Advanced analytics
- A/B testing
- No watermark

### Business ($199/month)
- Unlimited campaigns
- Priority generation
- Self-learning enabled
- API access
- Marketplace integrations

## Database Schema

### Tables
- **users**: User accounts, plans, limits, referrals
- **campaigns**: Product campaigns with status tracking
- **variants**: Platform-specific variants with metrics
- **winning_patterns**: Extracted patterns from successful campaigns
- **queue_tasks**: Generation queue with priority

## Platform Specifications

| Platform | Aspect Ratio | Style | Copy Length | Emoji |
|----------|-------------|-------|-------------|-------|
| Instagram | 1:1 | Bright | Short | ✅ |
| TikTok | 9:16 | Dynamic | Medium | ✅ |
| Amazon | 16:9 | Clean | Long | ❌ |
| Wildberries | 1:1 | Minimal | Short | ❌ |
| Ozon | 1:1 | Infographic | Medium | ❌ |

## Roadmap

### Phase 1 (Current - MVP)
- ✅ Multi-platform generation (mock)
- ✅ A/B testing simulation
- ✅ Self-learning patterns
- ✅ Mock marketplace publishing
- ✅ Subscription tiers

### Phase 2 (Next)
- [ ] Real AI integration (DALL-E, Midjourney API)
- [ ] Actual Wildberries/Ozon API integration
- [ ] Real payment processing
- [ ] Web dashboard for analytics

### Phase 3 (Future)
- [ ] ML model for predicting best variants
- [ ] Automatic campaign optimization
- [ ] API for external integrations
- [ ] Multi-language support

## Tech Stack

- **Framework**: aiogram 3 (Telegram Bot API)
- **Database**: SQLite with aiosqlite
- **Language**: Python 3.10+
- **Architecture**: Async/await, FSM, priority queue

## Development

### Running Tests
```bash
# TODO: Add tests
pytest
```

### Code Structure
- All services are async
- Database uses connection pooling
- Queue system with priority support
- FSM for multi-step dialogs

## Contributing

This is a personal project. For questions or suggestions, open an issue.

## License

MIT License

## Author

Danil Romanovsky ([@romanovskayalm23-ux](https://github.com/romanovskayalm23-ux))

---

**Note**: This is an MVP with mock generation and marketplace integrations. Production deployment requires:
1. Real AI API integration (OpenAI, Midjourney, etc.)
2. Marketplace API credentials and integration
3. Payment processing setup
4. Production database (PostgreSQL recommended)
5. Proper error handling and monitoring
