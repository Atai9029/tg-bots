from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("8781021259:AAGvabziD3IqAIcC_ruIuKGnzk2dmYO1f_M", "")
    google_api_key: str = os.getenv("AIzaSyAwqYWUeaSDjHcaWy4TBk8B2FluXhu28RI", "")
    database_path: str = os.getenv("DATABASE_PATH", "bot_data.sqlite3")
    uploads_dir: str = os.getenv("UPLOADS_DIR", "uploads")

    @property
    def database_url(self) -> str:
        return self.database_path


settings = Settings()
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
