"""Polls MeTube for its queue and history."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MeTubeClient, MeTubeError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type MeTubeConfigEntry = ConfigEntry[MeTubeCoordinator]


@dataclass
class MeTubeData:
    """What MeTube reports, split the way the entities use it."""

    queue: list[dict[str, Any]] = field(default_factory=list)
    finished: list[dict[str, Any]] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def last_finished(self) -> dict[str, Any] | None:
        return max(self.finished, key=lambda d: d.get("timestamp") or 0, default=None)


class MeTubeCoordinator(DataUpdateCoordinator[MeTubeData]):
    """Keeps one MeTube server's state up to date."""

    config_entry: MeTubeConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: MeTubeConfigEntry, client: MeTubeClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.versions: dict[str, Any] = {}

    async def _async_update_data(self) -> MeTubeData:
        try:
            history = await self.client.history()
        except MeTubeError as err:
            raise UpdateFailed(str(err)) from err
        done = history.get("done", [])
        return MeTubeData(
            queue=history.get("queue", []) + history.get("pending", []),
            finished=[d for d in done if d.get("status") != "error"],
            failed=[d for d in done if d.get("status") == "error"],
        )
