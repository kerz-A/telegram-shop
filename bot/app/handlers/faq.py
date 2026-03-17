import logging

from aiogram import Router
from aiogram.types import (
    ChosenInlineResult,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from bot.app.db.engine import async_session
from bot.app.db.repositories.repo import FAQRepo

logger = logging.getLogger(__name__)

router = Router(name="faq")


@router.inline_query()
async def faq_inline_query(inline_query: InlineQuery):
    """
    Search FAQ via inline query.
    Empty query → popular questions.
    """
    query = inline_query.query.strip()

    async with async_session() as session:
        repo = FAQRepo(session)
        faqs = await repo.search(query, limit=10)

    results = []
    for faq in faqs:
        results.append(
            InlineQueryResultArticle(
                id=str(faq.id),
                title=faq.question,
                description=faq.answer[:100],
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"<b>❓ {faq.question}</b>\n\n"
                        f"{faq.answer}"
                    ),
                    parse_mode="HTML",
                ),
            )
        )

    await inline_query.answer(results, cache_time=60, is_personal=False)


@router.chosen_inline_result()
async def faq_chosen(chosen: ChosenInlineResult):
    """Track FAQ popularity when user selects an answer."""
    try:
        faq_id = int(chosen.result_id)
        async with async_session() as session:
            repo = FAQRepo(session)
            await repo.increment_popularity(faq_id)
    except (ValueError, Exception) as e:
        logger.warning("Failed to track FAQ popularity: %s", e)
