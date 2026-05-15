from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    BOT_TOKEN: str

    MAX_SEARCH_RESULTS: int = 5
    MAX_FILE_SIZE_MB: int = 50
    SEARCH_CACHE_TTL: int = 300

    DOWNLOAD_PATH: Path = BASE_DIR / 'data' / 'downloads'

    LOG_LEVEL: str = 'INFO'
    LOG_FILE: Path = BASE_DIR / 'logs' / 'bot.log'

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f'LOG_LEVEL must be one of {sorted(allowed)}')
        return upper

    @field_validator('MAX_SEARCH_RESULTS')
    @classmethod
    def validate_max_results(cls, v: int) -> int:
        if not 1 <= v <= 15:
            raise ValueError('MAX_SEARCH_RESULTS must be between 1 and 15')
        return v


settings = Settings()
