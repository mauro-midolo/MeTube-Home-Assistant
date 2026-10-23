"""Sensors for the MeTube queue and history."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MeTubeConfigEntry, MeTubeData
from .entity import MeTubeEntity


def _titles(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"titles": [i.get("title") or i.get("url") for i in items]}


def _last(data: MeTubeData) -> dict[str, Any]:
    last = data.last_finished or {}
    return {k: last.get(k) for k in ("url", "filename", "folder", "format")}


@dataclass(frozen=True, kw_only=True)
class MeTubeSensorDescription(SensorEntityDescription):
    value_fn: Callable[[MeTubeData], Any]
    attrs_fn: Callable[[MeTubeData], dict[str, Any]]


SENSORS = (
    MeTubeSensorDescription(
        key="queue",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: len(d.queue),
        attrs_fn=lambda d: _titles(d.queue),
    ),
    MeTubeSensorDescription(
        key="finished",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: len(d.finished),
        attrs_fn=lambda d: _titles(d.finished),
    ),
    MeTubeSensorDescription(
        key="failed",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: len(d.failed),
        attrs_fn=lambda d: {
            "errors": {i.get("title") or i.get("url"): i.get("msg") or i.get("error") for i in d.failed}
        },
    ),
    MeTubeSensorDescription(
        key="last_download",
        value_fn=lambda d: (d.last_finished or {}).get("title"),
        attrs_fn=_last,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeTubeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(MeTubeSensor(entry.runtime_data, d) for d in SENSORS)


class MeTubeSensor(MeTubeEntity, SensorEntity):
    entity_description: MeTubeSensorDescription

    def __init__(self, coordinator, description: MeTubeSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.entity_description.attrs_fn(self.coordinator.data)
