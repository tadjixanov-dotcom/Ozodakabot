# 🌍 Ozodaka News Bot

Dunyo yangiliklarini ishonchli xalqaro manbalardan avtomatik yig'ib, tahlil qilib,
takroriylarni filtrlab, **o'zbek tilida** Telegram orqali yetkazib beruvchi bot.

## Imkoniyatlar

- 📡 14+ RSS manbadan avtomatik yig'ish (BBC, Al Jazeera, Guardian, Kun.uz, Gazeta.uz, IEEE Spectrum, Defense News va boshqalar)
- 🗂 6 ta kategoriya: urushlar/geosiyosat, Markaziy Osiyo, robototexnika, mudofaa sanoati, sun'iy intellekt, global siyosat-iqtisod
- 🔁 Dublikatlarni aniqlash (URL + hash + sarlavha o'xshashligi); bir nechta manbada tasdiqlangan yangilik reytingi oshadi
- ⭐ Muhimlik darajasini hisoblash (kontent signali + manba ishonchliligi + yangilik + tasdiqlar), clickbait pasaytiriladi
- 🇺🇿 AI orqali o'zbekchaga tarjima va 2-4 gaplik qisqartirish (Claude API); AIsiz ham to'liq ishlaydi
- 👍 Baholash tugmalari (👎 😐 👍 🔥 🚫) va shaxsiy **gibrid tavsiya algoritmi** — yoqmagan mavzular kamayadi, favqulodda muhim yangiliklar baribir yetib boradi
- ⚡ 3 ta rejim: real-time / dayjest / aralash; tungi jim rejim; kunlik limit
- 🛠 Admin panel: statistika, manbalarni boshqarish, broadcast
- 🐳 Docker bilan bir buyruqda ishga tushirish

## Arxitektura

```
RSS manbalar → Kollektor (httpx+feedparser) → Tozalash (BeautifulSoup)
   → Dedup (hash + o'xshashlik) → Muhimlik balli → AI tarjima (ixtiyoriy)
   → SQLite/PostgreSQL → Tavsiya algoritmi (foydalanuvchi profili)
   → Yetkazish (real-time / dayjest, limitlar, retry) → Telegram
```

Yangilik balli: `final_score = importance + interest + freshness + source_score − dislike_similarity_penalty`.
Foydalanuvchi bahosi profilga yoziladi (kalit so'z og'irliklari), keyingi yangiliklarni
tanlashda Jaccard o'xshashligi orqali qo'llanadi. 10-15% exploration filter pufagini oldini oladi.

## O'rnatish

### 1. Python o'rnatish

Python **3.11+** kerak. [python.org](https://www.python.org/downloads/) yoki Windows'da: `py install`.

### 2. Virtual environment

```bash
cd Ozodakabot
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Kutubxonalar

```bash
pip install -r requirements.txt
```

### 4. Telegram token olish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` → bot nomi va username kiriting
3. Berilgan tokenni nusxa oling

### 5. .env faylini to'ldirish

```bash
# Windows: copy .env.example .env
cp .env.example .env
```

`.env` ichida:
- `BOT_TOKEN=` — BotFather tokeni
- `ADMIN_IDS=` — sizning Telegram ID'ingiz ([@userinfobot](https://t.me/userinfobot) orqali bilib oling). Bir nechta bo'lsa vergul bilan.

### 6-7. Ma'lumotlar bazasi va migratsiya

Bot birinchi ishga tushishda jadvallarni o'zi yaratadi. Alembic bilan qilish uchun:

```bash
alembic upgrade head
```

Keyingi sxema o'zgarishlarida: `alembic revision --autogenerate -m "izoh"` → `alembic upgrade head`.

### 8. Lokal ishga tushirish

```bash
python -m app.main
```

Telegram'da botga `/start` yozing. Yangiliklar har 15 daqiqada yig'iladi.
Darhol sinash uchun: `python -m scripts.collect_once` keyin botda `/digest`.

### 9. Docker orqali

```bash
docker compose up -d --build
docker compose logs -f bot
```

### 10. Serverga joylashtirish

**Railway (tavsiya etiladi):**

1. [railway.app](https://railway.app) → New Project → **Deploy from GitHub repo** → shu repozitoriyni tanlang
2. Railway `Dockerfile` ni avtomatik topib build qiladi (`railway.json` sozlangan)
3. **Variables** bo'limida qo'shing: `BOT_TOKEN`, `ADMIN_IDS`, `AI_PROVIDER=gemini`, `AI_API_KEY`, `AI_MODEL=gemini-2.5-flash`
4. Ma'lumotlar yo'qolmasligi uchun ikkidan birini tanlang:
   - **PostgreSQL** (tavsiya): projectga "+ New → Database → PostgreSQL" qo'shing, bot servisiga `DATABASE_URL=${{Postgres.DATABASE_URL}}` variable bering (bot `postgres://` URL'ni avtomatik `postgresql+asyncpg://` ga o'giradi)
   - **Volume**: bot servisiga Volume ulang (mount path `/data`) va `DATABASE_URL=sqlite+aiosqlite:////data/news_bot.db` qo'ying

**Oddiy VPS:**

1. Serverga loyihani yuklang (git yoki scp)
2. `.env` yarating (tokenlar bilan)
3. `docker compose up -d --build`
4. Yangilash: `git pull && docker compose up -d --build`

### 11. Yangi RSS manba qo'shish

**1-usul:** `config/sources.json` ga yangi obyekt qo'shing (bot qayta ishga tushganda avtomatik yuklanadi):

```json
{ "name": "Manba nomi", "url": "https://.../rss", "source_type": "rss",
  "category": "ai", "language": "en", "reliability_score": 0.8, "is_active": true }
```

**2-usul (admin, botning o'zida):** `/add_source Nom | https://url/rss | ai`

Kategoriya sluglari: `wars`, `region`, `robotics`, `defense`, `ai`, `global`.

### 12. AI tarjima ulash

**Gemini (tavsiya etiladi — bepul tarif bor):**

```env
AI_PROVIDER=gemini
AI_API_KEY=AIza...
AI_MODEL=gemini-2.5-flash
```

API kaliti: [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — Google
hisobingiz bilan kirib "Create API key" bosing.

**Anthropic Claude (muqobil):**

```env
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-...
AI_MODEL=claude-opus-4-8
```

AI o'chirilgan yoki kalit xato bo'lsa bot manbadagi original matnni qisqartirib
yuboradi — hech narsa buzilmaydi.

Yangi provayder qo'shish: `app/news/translation/service.py` da `BaseTranslator` dan
meros oling va `build_translator()` ga ulang.

### 13. Admin ID o'rnatish

`.env` da `ADMIN_IDS=123456789` (bir nechta: `123,456`). Admin komandalar:
`/admin`, `/admin_sources`, `/add_source`, `/broadcast`.

### 14. Testlarni ishga tushirish

```bash
pytest -v
```

Testlar qamrovi: HTML tozalash, dublikat aniqlash, muhimlik reytingi, tavsiya algoritmi
(salbiy baholangan mavzuni pasaytirish, critical override), feedback saqlash (dublikatsiz),
xabar formatlash (HTML escape, Telegram limiti), ishlamaydigan manbada pipeline yiqilmasligi,
callback validatsiyasi.

### 15. Muammolarni aniqlash

- Loglar terminalda (`LOG_LEVEL=DEBUG` bilan batafsil) yoki `docker compose logs -f bot`
- Ishlamayotgan manbalar: botda `/admin` (⚠️ bilan ko'rsatiladi)
- Yig'ishni qo'lda tekshirish: `python -m scripts.collect_once`
- Bot javob bermasa: BOT_TOKEN to'g'riligini va internetni tekshiring
- `no such table` xatosi: `alembic upgrade head` yoki botni qayta ishga tushiring

## Loyiha strukturasi

```
app/
├── bot/            # aiogram handlerlar, keyboardlar, middleware, filterlar
├── core/           # config (pydantic), logging (loguru), security
├── database/       # SQLAlchemy modellar, repositorylar, seed, sessiya
├── news/           # kollektorlar, tozalash, dedup, tarjima, reyting
├── recommendations/# profil, scoring, similarity
├── scheduler/      # APScheduler ishlari
├── services/       # pipeline, delivery, formatter
└── main.py         # kirish nuqtasi
config/sources.json # manbalar ro'yxati
alembic/            # migratsiyalar
tests/              # pytest testlari
```

## Mualliflik huquqi

Bot maqolalarning to'liq matnini nusxalamaydi — faqat sarlavha, qisqa mazmun (2-4 gap)
va **original manbaga havola** yuboriladi. Tarjimada faktlar o'zgartirilmaydi.
