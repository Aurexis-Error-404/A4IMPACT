from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).parent  # backend/
_DEFAULT_DATA_PATH = str(_HERE.parent / "crop_data" / "season_report_summary.json")
_ENV_FILE = str(_HERE / ".env")


class Settings(BaseSettings):
    groq_api_key: str = ""
    allowed_origin: str = "http://localhost:3000"
    data_path: str = _DEFAULT_DATA_PATH

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _validate_paths(self) -> "Settings":
        if not Path(self.data_path).is_absolute():
            raise ValueError(
                f"DATA_PATH must be an absolute path; got: {self.data_path!r}. "
                "Use an absolute path or omit DATA_PATH to use the default."
            )
        return self
