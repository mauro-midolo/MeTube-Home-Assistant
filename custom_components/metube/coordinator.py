"""Polls MeTube for its queue and history."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MeTubeClient, MeTubeError
from .const import DOMAIN, EVENT_DOWNLOAD_FAILED, EVENT_DOWNLOAD_FINISHED, SCAN_INTERVAL

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
        # Completed downloads already seen; None until the first refresh, so
        # the history MeTube already has does not fire events at startup.
        self._seen_done: set[tuple[Any, Any]] | None = None

    async def _async_update_data(self) -> MeTubeData:
        try:
            history = await self.client.history()
        except MeTubeError as err:
            raise UpdateFailed(str(err)) from err
        done = history.get("done", [])
        self._fire_new_done_events(done)
        return MeTubeData(
            queue=history.get("queue", []) + history.get("pending", []),
            finished=[d for d in done if d.get("status") != "error"],
            failed=[d for d in done if d.get("status") == "error"],
        )

    def _fire_new_done_events(self, done: list[dict[str, Any]]) -> None:
        # Re-adding a URL creates a new record with a new timestamp.
        keys = {(d.get("url"), d.get("timestamp")) for d in done}
        if self._seen_done is not None:
            for item in done:
                if (item.get("url"), item.get("timestamp")) in self._seen_done:
                    continue
                if item.get("status") == "finished":
                    event = EVENT_DOWNLOAD_FINISHED
                elif item.get("status") == "error":
                    event = EVENT_DOWNLOAD_FAILED
                else:
                    continue
                self.hass.bus.async_fire(
                    event,
                    {
                        "config_entry_id": self.config_entry.entry_id,
                        "url": item.get("url"),
                        "title": item.get("title"),
                        "filename": item.get("filename"),
                        "folder": item.get("folder"),
                        "download_type": item.get("download_type"),
                        "format": item.get("format"),
                        "error": item.get("msg") or item.get("error"),
                    },
                )
        self._seen_done = keys
