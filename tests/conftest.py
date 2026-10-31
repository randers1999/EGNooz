from __future__ import annotations

from pathlib import Path

import pytest

from egnooz.config import Settings

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    data = tmp_path / "data"
    return Settings(
        repo_root=REPO,
        data_dir=data,
        secret_key="test-secret-key-not-for-production",
        review_password="test-pass",
        session_cookie_secure=False,
        review_base_url="https://krystalbbs.net",
        tom_email="tom@example.test",
        send_draft_ready_email=False,
    )
