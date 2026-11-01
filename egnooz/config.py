from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from egnooz import TIMEZONE_NAME

DEFAULT_HOST = "egnooz.krystalbbs.net"
DEFAULT_BASE_URL = f"https://{DEFAULT_HOST}"
DEFAULT_ENV_PATH = Path.home() / ".config" / "egnooz" / "egnooz.env"


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def discover_env_file() -> Path | None:
    explicit = os.environ.get("EGNOOZ_ENV_FILE")
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    for candidate in (DEFAULT_ENV_PATH, Path.cwd() / ".env"):
        if candidate.is_file():
            return candidate
    return None


def load_env_file() -> Path | None:
    path = discover_env_file()
    if path is not None:
        load_dotenv(path, override=False)
    return path


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _default_repo_root() -> Path:
    env = os.environ.get("EGNOOZ_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    repo_root: Path
    data_dir: Path
    timezone: str = TIMEZONE_NAME
    bind: str = "127.0.0.1"
    port: int = 8080
    review_base_url: str = DEFAULT_BASE_URL
    secret_key: str = ""
    review_password: str = ""
    session_cookie_secure: bool = True
    tom_email: str = ""
    resend_api_key: str = ""
    resend_from: str = ""
    subscriber_emails: list[str] = field(default_factory=list)
    send_draft_ready_email: bool = True
    env_file: Path | None = None

    @property
    def drafts_dir(self) -> Path:
        return self.data_dir / "drafts"

    @property
    def published_dir(self) -> Path:
        return self.data_dir / "published"

    @property
    def state_dir(self) -> Path:
        return self.data_dir / "state"

    @property
    def sources_path(self) -> Path:
        return self.repo_root / "sources.yaml"

    @property
    def places_path(self) -> Path:
        return self.repo_root / "places.yaml"

    def ensure_dirs(self) -> None:
        for path in (self.drafts_dir, self.published_dir, self.state_dir):
            path.mkdir(parents=True, exist_ok=True)

    def review_url(self, path: str = "/") -> str:
        base = self.review_base_url.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        return base + path

    def email_ready(self) -> bool:
        return bool(self.resend_api_key and self.resend_from and self.tom_email)

    def missing_for_serve(self) -> list[str]:
        missing = []
        if not self.secret_key:
            missing.append("SECRET_KEY")
        if not self.review_password:
            missing.append("REVIEW_PASSWORD")
        return missing


def load_settings() -> Settings:
    env_file = load_env_file()
    repo_root = _default_repo_root()
    data_default = Path.home() / "egnooz-data"
    data_dir = Path(os.environ.get("EGNOOZ_DATA_DIR", str(data_default))).expanduser().resolve()
    base_url = os.environ.get("REVIEW_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    secure_default = base_url.startswith("https://")
    return Settings(
        repo_root=repo_root,
        data_dir=data_dir,
        timezone=os.environ.get("EGNOOZ_TZ", TIMEZONE_NAME),
        bind=os.environ.get("EGNOOZ_BIND", "127.0.0.1"),
        port=int(os.environ.get("EGNOOZ_PORT", "8080")),
        review_base_url=base_url,
        secret_key=os.environ.get("SECRET_KEY", ""),
        review_password=os.environ.get("REVIEW_PASSWORD", ""),
        session_cookie_secure=_truthy(
            os.environ.get("SESSION_COOKIE_SECURE"), default=secure_default
        ),
        tom_email=os.environ.get("TOM_EMAIL", "").strip(),
        resend_api_key=os.environ.get("RESEND_API_KEY", "").strip(),
        resend_from=os.environ.get("RESEND_FROM", "").strip(),
        subscriber_emails=_csv(os.environ.get("SUBSCRIBER_EMAILS")),
        send_draft_ready_email=_truthy(
            os.environ.get("SEND_DRAFT_READY_EMAIL"), default=True
        ),
        env_file=env_file,
    )
