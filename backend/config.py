from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_DATA_PATH = str(Path(__file__).parent.parent / "crop_data" / "season_report_summary.json")


class Settings(BaseSettings):
    groq_api_key: str = ""
    allowed_origin: str = "http://localhost:3000"
    data_path: str = _DEFAULT_DATA_PATH

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
