"""Base entity for MeTube."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MeTubeCoordinator


class MeTubeEntity(CoordinatorEntity[MeTubeCoordinator]):
    """An entity that belongs to the MeTube service device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MeTubeCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        versions = coordinator.versions
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="MeTube",
            manufacturer="MeTube",
            model=f"yt-dlp {versions.get('yt-dlp', '?')}",
            sw_version=versions.get("version"),
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator.client.url,
        )
