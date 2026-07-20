"""Ishlamayotgan manba pipeline'ni to'xtatib qo'ymasligi testi."""
from datetime import datetime, timezone

import app.services.pipeline as pipeline_module
from app.database.models import Category, Source
from app.news.collectors.base import RawItem
from app.news.translation.service import NoopTranslator
from app.services.pipeline import collect_and_process


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def test_broken_source_does_not_stop_pipeline(db_factory, monkeypatch):
    async with db_factory() as session:
        cat = Category(name="AI", slug="ai")
        session.add(cat)
        await session.flush()
        session.add(Source(name="Broken", url="https://broken.test/rss", category_id=cat.id))
        session.add(Source(name="Working", url="https://working.test/rss", category_id=cat.id))
        await session.commit()

    async def fake_fetch(url: str, timeout: float = 20.0):
        if "broken" in url:
            raise ConnectionError("DNS failure")
        return [RawItem(
            title="OpenAI announces new robotics model for factories",
            summary="The company revealed a new model designed for industrial robots.",
            url="https://working.test/article-1",
            external_id="a1",
            published_at=_now(),
        )]

    monkeypatch.setattr(pipeline_module, "fetch_rss", fake_fetch)

    new_ids = await collect_and_process(db_factory, NoopTranslator())
    assert len(new_ids) == 1  # ishlaydigan manbadan maqola olindi

    async with db_factory() as session:
        from sqlalchemy import select
        sources = (await session.execute(select(Source))).scalars().all()
        broken = next(s for s in sources if s.name == "Broken")
        working = next(s for s in sources if s.name == "Working")
        assert broken.last_error is not None
        assert working.last_error is None
        assert working.last_success_at is not None


async def test_same_article_not_duplicated(db_factory, monkeypatch):
    async with db_factory() as session:
        cat = Category(name="AI", slug="ai")
        session.add(cat)
        await session.flush()
        session.add(Source(name="Feed", url="https://feed.test/rss", category_id=cat.id))
        await session.commit()

    item = RawItem(
        title="New AI regulation approved by parliament",
        summary="Lawmakers approved sweeping new rules for artificial intelligence.",
        url="https://feed.test/article-2",
        external_id="a2",
        published_at=_now(),
    )

    async def fake_fetch(url: str, timeout: float = 20.0):
        return [item]

    monkeypatch.setattr(pipeline_module, "fetch_rss", fake_fetch)

    first = await collect_and_process(db_factory, NoopTranslator())
    second = await collect_and_process(db_factory, NoopTranslator())
    assert len(first) == 1
    assert len(second) == 0  # bir xil yangilik qayta saqlanmaydi
