"""The MeTube integration: download with yt-dlp from Home Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import MeTubeClient, MeTubeError
from .const import (
    CONF_DOWNLOAD_TYPE,
    CONF_FOLDER,
    CONF_FORMAT,
    CONF_QUALITY,
    DEFAULT_OPTIONS,
    DOMAIN,
    DOWNLOAD_TYPES,
)
from .coordinator import MeTubeConfigEntry, MeTubeCoordinator

PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.TEXT]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_URL = "url"
ATTR_PLAYLIST_ITEM_LIMIT = "playlist_item_limit"

SERVICE_DOWNLOAD = "download"
DOWNLOAD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_URL): cv.string,
        vol.Optional(CONF_DOWNLOAD_TYPE): vol.In(DOWNLOAD_TYPES),
        vol.Optional(CONF_FORMAT): cv.string,
        vol.Optional(CONF_QUALITY): cv.string,
        vol.Optional(CONF_FOLDER): cv.string,
        vol.Optional(ATTR_PLAYLIST_ITEM_LIMIT): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


async def async_download(
    entry: MeTubeConfigEntry, url: str, **overrides: Any
) -> None:
    """Queue a download, filling in what the caller left out from the entry's options."""
    opts = {**DEFAULT_OPTIONS, **entry.options}
    opts.update({k: v for k, v in overrides.items() if v is not None})
    try:
        await entry.runtime_data.client.add(
            url.strip(),
            opts[CONF_DOWNLOAD_TYPE],
            opts[CONF_FORMAT],
            opts[CONF_QUALITY],
            folder=opts[CONF_FOLDER] or None,
            playlist_item_limit=opts.get(ATTR_PLAYLIST_ITEM_LIMIT),
        )
    except MeTubeError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="download_failed",
            translation_placeholders={"error": str(err)},
        ) from err
    await entry.runtime_data.async_request_refresh()


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the download action."""

    async def handle_download(call: ServiceCall) -> None:
        entries: list[MeTubeConfigEntry] = [
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if e.state is ConfigEntryState.LOADED
        ]
        if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
            entries = [e for e in entries if e.entry_id == entry_id]
        if not entries:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="not_loaded"
            )
        data = dict(call.data)
        data.pop(ATTR_CONFIG_ENTRY_ID, None)
        await async_download(entries[0], data.pop(ATTR_URL), **data)

    hass.services.async_register(
        DOMAIN, SERVICE_DOWNLOAD, handle_download, schema=DOWNLOAD_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MeTubeConfigEntry) -> bool:
    """Set up MeTube from a config entry."""
    client = MeTubeClient(async_get_clientsession(hass), entry.data[CONF_URL])
    try:
        version = await client.version()
    except MeTubeError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = MeTubeCoordinator(hass, entry, client)
    coordinator.versions = version
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MeTubeConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
