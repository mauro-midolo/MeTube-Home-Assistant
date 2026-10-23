"""Tests for the config and options flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.metube.const import DEFAULT_OPTIONS, DOMAIN

from .conftest import URL


async def test_user_flow(hass: HomeAssistant, metube) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"url": URL + "/"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"url": URL}
    assert result["options"] == DEFAULT_OPTIONS


async def test_user_flow_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/version", status=404)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"url": URL})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_duplicate(hass: HomeAssistant, entry, metube) -> None:
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"url": URL})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, entry, metube) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"download_type": "audio", "format": "mp4", "quality": "best"}
    )
    assert result["errors"] == {"format": "format_mismatch"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"download_type": "video", "format": "mp4", "quality": "1080"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"download_type": "video", "format": "mp4", "quality": "1080", "folder": ""}


async def test_user_flow_suggests_installed_app(hass: HomeAssistant, metube) -> None:
    app = MagicMock(slug="a1b2c3d4_metube")
    client = MagicMock()
    client.addons.list = AsyncMock(return_value=[MagicMock(slug="core_mosquitto"), app])
    with (
        patch("custom_components.metube.config_flow.is_hassio", return_value=True),
        patch("homeassistant.components.hassio.get_supervisor_client", return_value=client),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    url_key = next(k for k in result["data_schema"].schema if k == "url")
    assert url_key.description["suggested_value"] == "http://a1b2c3d4-metube:8081"
