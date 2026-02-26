from aiogram import Router

from . import registration, breakfast, excursions, guide, bnovo, support, linen, ai_assistant


def setup_routers() -> Router:
    router = Router()
    router.include_router(registration.router)
    router.include_router(breakfast.router)
    router.include_router(excursions.router)
    router.include_router(guide.router)
    router.include_router(bnovo.router)
    router.include_router(support.router)
    router.include_router(linen.router)
    router.include_router(ai_assistant.router)
    return router

