"""A text box: paste a link and MeTube downloads it with the default options."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import async_download
from .coordinator import MeTubeConfigEntry
from .entity import MeTubeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeTubeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([MeTubeLinkText(entry.runtime_data, "link")])


class MeTubeLinkText(MeTubeEntity, TextEntity):
    # Always shows empty, so the box is ready for the next link once one is sent.
    _attr_native_value = ""
    _attr_native_max = 255

    async def async_set_value(self, value: str) -> None:
        if value.strip():
            await async_download(self.coordinator.config_entry, value)
        self.async_write_ha_state()
