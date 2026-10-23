"""Fixtures for the MeTube tests."""

import pytest

from homeassistant.const import CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.metube.const import DEFAULT_OPTIONS, DOMAIN

URL = "http://local-metube:8081"

HISTORY = {
    "queue": [{"url": "https://y/1", "title": "In download", "status": "downloading"}],
    "pending": [],
    "done": [
        {"url": "https://y/2", "title": "Old song", "status": "finished", "timestamp": 1, "filename": "Old song.mp3"},
        {"url": "https://y/3", "title": "New song", "status": "finished", "timestamp": 2, "filename": "New song.mp3"},
        {"url": "https://y/4", "title": "Broken", "status": "error", "timestamp": 3, "msg": "ERROR: unavailable"},
    ],
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN, title="MeTube", data={CONF_URL: URL}, options=DEFAULT_OPTIONS
    )


@pytest.fixture
def metube(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    aioclient_mock.get(f"{URL}/version", json={"yt-dlp": "2026.10.21", "version": "2026.10.22"})
    aioclient_mock.get(f"{URL}/history", json=HISTORY)
    aioclient_mock.post(f"{URL}/add", json={"status": "ok"})
    aioclient_mock.post(f"{URL}/delete", json={"status": "ok"})
    return aioclient_mock
