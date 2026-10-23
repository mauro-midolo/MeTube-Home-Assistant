"""Config and options flow for MeTube."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.hassio import is_hassio
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import MeTubeClient, MeTubeError
from .const import (
    AUDIO_FORMATS,
    CONF_DOWNLOAD_TYPE,
    CONF_FOLDER,
    CONF_FORMAT,
    CONF_QUALITY,
    DEFAULT_OPTIONS,
    DEFAULT_URL,
    DOMAIN,
    DOWNLOAD_TYPES,
    QUALITIES,
    VIDEO_FORMATS,
)
from .coordinator import MeTubeConfigEntry

_LOGGER = logging.getLogger(__name__)


async def _async_app_url(hass: HomeAssistant) -> str:
    """Find the MeTube app among the installed apps and return its internal URL.

    The app's hostname depends on where it was installed from: "local-metube"
    for a local copy, "<repository hash>-metube" when added from GitHub.
    """
    if not is_hassio(hass):
        return DEFAULT_URL
    from aiohasupervisor import SupervisorError  # noqa: PLC0415
    from homeassistant.components.hassio import get_supervisor_client  # noqa: PLC0415

    try:
        apps = await get_supervisor_client(hass).addons.list()
    except SupervisorError as err:
        _LOGGER.debug("Cannot list apps: %s", err)
        return DEFAULT_URL
    for app in apps:
        if app.slug == "metube" or app.slug.endswith("_metube"):
            return f"http://{app.slug.replace('_', '-')}:8081"
    return DEFAULT_URL


def _select(options: list[str], key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options, translation_key=key, mode=SelectSelectorMode.DROPDOWN
        )
    )


class MeTubeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Connect Home Assistant to a MeTube server."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            self._async_abort_entries_match({CONF_URL: url})
            client = MeTubeClient(async_get_clientsession(self.hass), url)
            try:
                await client.version()
            except MeTubeError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="MeTube", data={CONF_URL: url}, options=DEFAULT_OPTIONS
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_URL): TextSelector(
                            TextSelectorConfig(type=TextSelectorType.URL)
                        )
                    }
                ),
                user_input or {CONF_URL: await _async_app_url(self.hass)},
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(entry: MeTubeConfigEntry) -> MeTubeOptionsFlow:
        return MeTubeOptionsFlow()


class MeTubeOptionsFlow(OptionsFlowWithReload):
    """Default options used by the link box and by actions that leave them out."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            formats = AUDIO_FORMATS if user_input[CONF_DOWNLOAD_TYPE] == "audio" else VIDEO_FORMATS
            if user_input[CONF_FORMAT] not in formats:
                errors[CONF_FORMAT] = "format_mismatch"
            else:
                user_input.setdefault(CONF_FOLDER, "")
                return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_DOWNLOAD_TYPE): _select(DOWNLOAD_TYPES, CONF_DOWNLOAD_TYPE),
                vol.Required(CONF_FORMAT): _select(AUDIO_FORMATS + VIDEO_FORMATS, CONF_FORMAT),
                vol.Required(CONF_QUALITY): _select(QUALITIES, CONF_QUALITY),
                vol.Optional(CONF_FOLDER): TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or {**DEFAULT_OPTIONS, **self.config_entry.options}
            ),
            errors=errors,
        )
