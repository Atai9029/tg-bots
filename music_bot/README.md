# Music Bot

Telegram bot for searching YouTube and sending audio as MP3.

## Structure

```
music_bot/
├── main.py
├── config/settings.py
├── handlers/start.py
├── handlers/search.py
├── handlers/download.py
├── keyboards/inline.py
├── services/music_search.py
├── services/music_downloader.py
├── utils/logger.py
├── utils/helpers.py
├── utils/search_cache.py
├── requirements.txt
├── .env.example
└── README.md
```

## Run

1. `cp .env.example .env`
2. Put your Telegram bot token into `.env`
3. `pip install -r requirements.txt`
4. `python main.py`

## Notes

- FFmpeg must be installed on the system.
- The project uses aiogram 3.
