"""Tests for setup, entities and the download action."""

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_capture_events

from .conftest import HISTORY, URL


async def _setup(hass, entry):
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def _posts(mock, path):
    return [call[2] for call in mock.mock_calls if call[0] == "POST" and str(call[1]).endswith(path)]


async def test_entities(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED

    assert hass.states.get("sensor.metube_queue").state == "1"
    assert hass.states.get("sensor.metube_completed").state == "2"
    failed = hass.states.get("sensor.metube_failed")
    assert failed.state == "1"
    assert failed.attributes["errors"] == {"Broken": "ERROR: unavailable"}
    last = hass.states.get("sensor.metube_last_download")
    assert last.state == "New song"
    assert last.attributes["filename"] == "New song.mp3"


async def test_download_action_uses_defaults(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    await hass.services.async_call(
        "metube", "download", {"url": " https://youtu.be/abc "}, blocking=True
    )
    assert _posts(metube, "/add") == [
        {"url": "https://youtu.be/abc", "download_type": "audio", "format": "mp3", "quality": "best", "auto_start": True}
    ]


async def test_download_action_overrides(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    await hass.services.async_call(
        "metube",
        "download",
        {"url": "https://youtu.be/abc", "format": "flac", "folder": "Rock", "playlist_item_limit": 5},
        blocking=True,
    )
    assert _posts(metube, "/add")[0] == {
        "url": "https://youtu.be/abc",
        "download_type": "audio",
        "format": "flac",
        "quality": "best",
        "auto_start": True,
        "folder": "Rock",
        "playlist_item_limit": 5,
    }


async def test_download_rejected(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    metube.clear_requests()
    metube.post(f"{URL}/add", json={"status": "error", "msg": "ERROR: Unsupported URL"})
    with pytest.raises(HomeAssistantError, match="Unsupported URL"):
        await hass.services.async_call("metube", "download", {"url": "https://nope"}, blocking=True)


async def test_link_box(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": "text.metube_link_to_download", "value": "https://youtu.be/xyz"},
        blocking=True,
    )
    assert _posts(metube, "/add")[0]["url"] == "https://youtu.be/xyz"
    assert hass.states.get("text.metube_link_to_download").state == ""


async def test_clear_button(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.metube_clear_completed"}, blocking=True
    )
    assert _posts(metube, "/delete") == [{"ids": ["https://y/2", "https://y/3"], "where": "done"}]


async def test_not_ready(hass: HomeAssistant, entry, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/version", status=502)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_download_bad_request(hass: HomeAssistant, entry, metube) -> None:
    await _setup(hass, entry)
    metube.clear_requests()
    metube.post(f"{URL}/add", status=400, text="400: format must be one of ['any', 'ios', 'mp4'] for video")
    with pytest.raises(HomeAssistantError, match="format must be one of"):
        await hass.services.async_call(
            "metube", "download", {"url": "https://x", "download_type": "video"}, blocking=True
        )


async def test_italian_entity_ids(hass: HomeAssistant, entry, metube) -> None:
    hass.config.language = "it"
    await _setup(hass, entry)
    for entity_id in (
        "text.metube_link_da_scaricare",
        "sensor.metube_coda",
        "sensor.metube_completati",
        "sensor.metube_falliti",
        "sensor.metube_ultimo_download",
        "button.metube_svuota_completati",
    ):
        assert hass.states.get(entity_id), entity_id


async def test_events_for_new_downloads(hass: HomeAssistant, entry, metube) -> None:
    finished = async_capture_events(hass, "metube_download_finished")
    failed = async_capture_events(hass, "metube_download_failed")
    await _setup(hass, entry)
    # What MeTube already had at startup is not reported again.
    assert finished == [] and failed == []

    metube.clear_requests()
    metube.get(f"{URL}/history", json={**HISTORY, "done": HISTORY["done"] + [
        {"url": "https://y/5", "title": "Fresh", "status": "finished", "timestamp": 5, "filename": "Fresh.mp3", "folder": "Rock", "format": "mp3", "download_type": "audio"},
        {"url": "https://y/6", "title": "Gone", "status": "error", "timestamp": 6, "msg": "ERROR: Video unavailable"},
    ]})
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert [e.data["url"] for e in finished] == ["https://y/5"]
    assert finished[0].data["filename"] == "Fresh.mp3"
    assert finished[0].data["folder"] == "Rock"
    assert [e.data["error"] for e in failed] == ["ERROR: Video unavailable"]

    # A later poll with the same history fires nothing new.
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert len(finished) == 1 and len(failed) == 1
