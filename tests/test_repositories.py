from app.database.models import Article, Category, Source
from app.database.repositories.feedback import (
    get_or_create_profile, get_saved_articles, save_article, upsert_feedback,
)
from app.database.repositories.users import get_enabled_category_ids, get_or_create_user
from app.recommendations.profile_builder import update_profile_on_feedback


async def _setup_article(session) -> Article:
    cat = Category(name="AI", slug="ai")
    session.add(cat)
    await session.flush()
    src = Source(name="Test", url="https://t.test/rss", category_id=cat.id)
    session.add(src)
    await session.flush()
    article = Article(
        source_id=src.id, category_id=cat.id, original_title="AI news",
        url="https://t.test/1", content_hash="abc",
        keywords=["openai", "model", "release"], importance_score=0.5,
    )
    session.add(article)
    await session.commit()
    return article


async def test_user_created_with_all_categories(session):
    session.add(Category(name="AI", slug="ai"))
    session.add(Category(name="Wars", slug="wars"))
    await session.commit()

    user = await get_or_create_user(session, telegram_id=111, username="tester")
    assert user.id is not None
    enabled = await get_enabled_category_ids(session, user)
    assert len(enabled) == 2

    # Qayta chaqirilsa yangi foydalanuvchi yaratilmaydi
    same = await get_or_create_user(session, telegram_id=111, username="tester")
    assert same.id == user.id


async def test_feedback_upsert_no_duplicates(session):
    article = await _setup_article(session)
    user = await get_or_create_user(session, 222, "u2")

    fb1 = await upsert_feedback(session, user.id, article.id, "like")
    assert fb1.rating == 1

    # Qayta bosilsa — yangilanadi, ikkinchi yozuv paydo bo'lmaydi
    fb2 = await upsert_feedback(session, user.id, article.id, "dislike")
    assert fb2.id == fb1.id
    assert fb2.rating == -1
    assert fb2.feedback_type == "dislike"


async def test_saved_articles(session):
    article = await _setup_article(session)
    user = await get_or_create_user(session, 333, "u3")

    assert await save_article(session, user.id, article.id) is True
    assert await save_article(session, user.id, article.id) is False  # dublikat emas

    saved = await get_saved_articles(session, user.id)
    assert len(saved) == 1
    assert saved[0].id == article.id


async def test_profile_updated_on_feedback(session):
    article = await _setup_article(session)
    user = await get_or_create_user(session, 444, "u4")

    await update_profile_on_feedback(session, user.id, article, "love")
    profile = await get_or_create_profile(session, user.id)
    assert profile.positive_keywords.get("openai", 0) > 0
    assert profile.category_weights.get("ai", 0) > 0

    await update_profile_on_feedback(session, user.id, article, "less_topic")
    await session.refresh(profile)
    assert profile.negative_keywords.get("openai", 0) > 0
