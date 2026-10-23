"""Button that clears finished downloads from MeTube's list (files are kept)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MeTubeError
from .const import DOMAIN
from .coordinator import MeTubeConfigEntry
from .entity import MeTubeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeTubeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([MeTubeClearButton(entry.runtime_data, "clear_finished")])


class MeTubeClearButton(MeTubeEntity, ButtonEntity):
    async def async_press(self) -> None:
        ids = [d["url"] for d in self.coordinator.data.finished if d.get("url")]
        if not ids:
            return
        try:
            await self.coordinator.client.clear_done(ids)
        except MeTubeError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="request_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await self.coordinator.async_request_refresh()
