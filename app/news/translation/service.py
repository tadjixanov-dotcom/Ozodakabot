"""Tarjima va qisqartirish servisi — provayder almashtiriladigan arxitektura.

AI_PROVIDER bo'sh bo'lsa NoopTranslator ishlaydi (original matn qaytadi) —
bot AIsiz ham to'liq ishlashda davom etadi.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from loguru import logger

from app.core.config import Settings, get_settings
from app.news.parsers.cleaner import truncate_text


@dataclass(slots=True)
class TranslationResult:
    title: str
    summary: str
    translated: bool


class BaseTranslator(ABC):
    """Yangi AI provayder qo'shish uchun shu interfeysni amalga oshiring."""

    @abstractmethod
    async def translate(self, title: str, summary: str) -> TranslationResult: ...


class NoopTranslator(BaseTranslator):
    """AI mavjud bo'lmaganda: manbadagi matnning o'zi qisqartirilib qaytariladi."""

    async def translate(self, title: str, summary: str) -> TranslationResult:
        return TranslationResult(title=title, summary=truncate_text(summary, 400), translated=False)


_SCHEMA = {
    "type": "object",
    "properties": {
        "title_uz": {"type": "string"},
        "summary_uz": {"type": "string"},
    },
    "required": ["title_uz", "summary_uz"],
    "additionalProperties": False,
}

_SYSTEM_PROMPT = (
    "Sen yangiliklar tarjimoni va muharririsan. Berilgan yangilik sarlavhasi va matnini "
    "o'zbek tiliga (lotin alifbosida) tarjima qil.\n"
    "Qoidalar:\n"
    "- Sarlavha qisqa va aniq bo'lsin.\n"
    "- Mazmunni 2-4 ta qisqa gap bilan tushuntir.\n"
    "- Faktlarni o'zgartirma, shaxsiy fikr qo'shma.\n"
    "- Taxmin va tasdiqlangan faktlarni ajrat ('...deb taxmin qilinmoqda' kabi).\n"
    "- Sana, joy, kompaniya, davlat va shaxs nomlarini saqla."
)


class AnthropicTranslator(BaseTranslator):
    """Claude API orqali tarjima + qisqartirish. Xatolikda original matnga qaytadi."""

    def __init__(self, api_key: str, model: str) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._fallback = NoopTranslator()

    async def translate(self, title: str, summary: str) -> TranslationResult:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
                messages=[{
                    "role": "user",
                    "content": f"Sarlavha: {title}\n\nMatn: {truncate_text(summary, 1500)}",
                }],
            )
            if response.stop_reason == "refusal" or not response.content:
                return await self._fallback.translate(title, summary)
            text = next((b.text for b in response.content if b.type == "text"), "")
            data = json.loads(text)
            return TranslationResult(
                title=str(data["title_uz"]).strip()[:500],
                summary=truncate_text(str(data["summary_uz"]).strip(), 600),
                translated=True,
            )
        except Exception as exc:  # AI xatosi botni to'xtatmasligi kerak
            logger.warning("AI tarjima xatosi ({}): original matn ishlatiladi", exc)
            return await self._fallback.translate(title, summary)


_GEMINI_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title_uz": {"type": "STRING"},
        "summary_uz": {"type": "STRING"},
    },
    "required": ["title_uz", "summary_uz"],
}


class GeminiTranslator(BaseTranslator):
    """Google Gemini API orqali tarjima + qisqartirish. Xatolikda original matnga qaytadi.

    Sozlangan model 404 qaytarsa (Google eski modellarni o'chiradi), API'dan
    mavjud modellar ro'yxatini olib, ishlaydigan flash modelni o'zi tanlaydi.
    """

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._model_verified = False
        self._failed_models: set[str] = set()
        self._fallback = NoopTranslator()

    async def _list_models(self, client) -> list[str]:
        """generateContent qo'llab-quvvatlaydigan modellar ro'yxati."""
        response = await client.get(
            f"{self._BASE_URL}/models",
            headers={"x-goog-api-key": self._api_key},
            params={"pageSize": 100},
        )
        response.raise_for_status()
        models = []
        for m in response.json().get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                models.append(m.get("name", "").removeprefix("models/"))
        return models

    async def _resolve_model(self, client) -> None:
        """Sozlangan model ishlamasa, mavjudlaridan eng mosini tanlaydi.

        Diqqat: ro'yxatda bor model ham generateContent'da 404 qaytarishi mumkin
        (Google "no longer available to new users" qiladi) — bunday modellar
        _failed_models'ga tushadi va qayta tanlanmaydi.
        """
        try:
            available = await self._list_models(client)
        except Exception as exc:
            logger.warning("Gemini modellar ro'yxatini olib bo'lmadi: {}", exc)
            return
        available = [m for m in available if m not in self._failed_models]
        if not available:
            return
        if self._model in available:
            self._model_verified = True
            return
        # Afzallik: flash-latest alias > stabil flash (lite emas) > qolganlari
        def rank(name: str) -> tuple:
            return (
                name == "gemini-flash-latest",
                "flash" in name,
                "preview" not in name and "exp" not in name,
                "lite" not in name,
                name,
            )
        best = sorted(available, key=rank, reverse=True)[0]
        logger.warning(
            "Gemini modeli '{}' ishlamayapti — '{}' ishlatiladi. Mavjudlar: {}",
            self._model, best, ", ".join(available[:10]),
        )
        self._model = best
        self._model_verified = True

    async def translate(self, title: str, summary: str) -> TranslationResult:
        import httpx

        payload = {
            "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
            "contents": [{
                "parts": [{
                    "text": f"Sarlavha: {title}\n\nMatn: {truncate_text(summary, 1500)}"
                }],
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _GEMINI_SCHEMA,
                "maxOutputTokens": 1024,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if not self._model_verified:
                    await self._resolve_model(client)
                response = await client.post(
                    f"{self._BASE_URL}/models/{self._model}:generateContent",
                    headers={"x-goog-api-key": self._api_key},
                    json=payload,
                )
                if response.status_code == 404:
                    # Model 404 — ro'yxatda bo'lsa ham ishlamaydi (yangi
                    # kalitlar uchun yopilgan bo'lishi mumkin). Qora ro'yxatga
                    # olib, boshqasini tanlaymiz va bir marta qayta urinamiz.
                    self._failed_models.add(self._model)
                    self._model_verified = False
                    await self._resolve_model(client)
                    if self._model not in self._failed_models:
                        response = await client.post(
                            f"{self._BASE_URL}/models/{self._model}:generateContent",
                            headers={"x-goog-api-key": self._api_key},
                            json=payload,
                        )
                response.raise_for_status()
            body = response.json()
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            return TranslationResult(
                title=str(data["title_uz"]).strip()[:500],
                summary=truncate_text(str(data["summary_uz"]).strip(), 600),
                translated=True,
            )
        except Exception as exc:  # AI xatosi botni to'xtatmasligi kerak
            logger.warning("Gemini tarjima xatosi ({}): original matn ishlatiladi", exc)
            return await self._fallback.translate(title, summary)


def build_translator(settings: Settings | None = None) -> BaseTranslator:
    settings = settings or get_settings()
    provider = settings.ai_provider.strip().lower()
    if not settings.ai_api_key and provider:
        logger.warning("AI_API_KEY bo'sh — AIsiz rejim ishlatiladi")
        return NoopTranslator()
    if provider == "anthropic":
        logger.info("AI tarjima yoqildi: anthropic / {}", settings.ai_model)
        return AnthropicTranslator(settings.ai_api_key, settings.ai_model)
    if provider == "gemini":
        # Model nomi gemini'ga mos bo'lmasa standartini olamiz
        model = settings.ai_model if settings.ai_model.startswith("gemini") else "gemini-flash-latest"
        logger.info("AI tarjima yoqildi: gemini / {}", model)
        return GeminiTranslator(settings.ai_api_key, model)
    if provider:
        logger.warning("Noma'lum AI_PROVIDER '{}' — AIsiz rejim ishlatiladi", provider)
    return NoopTranslator()
