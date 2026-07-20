from aiogram import Router

from app.bot.handlers import (
    admin, callbacks, categories, digest, feedback_cmd, help_cmd, saved, settings_cmd,
    sources_cmd, start,
)


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(categories.router)
    root.include_router(settings_cmd.router)
    root.include_router(digest.router)
    root.include_router(saved.router)
    root.include_router(feedback_cmd.router)
    root.include_router(sources_cmd.router)
    root.include_router(help_cmd.router)
    root.include_router(admin.router)
    root.include_router(callbacks.router)
    return root
