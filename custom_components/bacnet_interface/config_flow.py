"""Config flow for Hello World integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from aioecopanel import (DeviceDict, EcoPanelConnectionError,
                         EcoPanelEmptyResponseError, Interface)
from homeassistant.components import dhcp, network, onboarding, zeroconf
from homeassistant.components.hassio import HassioServiceInfo
from homeassistant.config_entries import (CONN_CLASS_LOCAL_PUSH, ConfigEntry,
                                          ConfigFlow, OptionsFlow)
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER  # pylint:disable=unused-import

_LOGGER = LOGGER


class EcoPanelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the EcoPanel."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""

        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        adapters = await network.async_get_adapters(self.hass)

        # Get functional IP address for the user...
        for adapter in adapters:
            if adapter is None:
                ip_addr = "127.0.0.1"
                break
            for ip_info in adapter["ipv4"]:
                try:
                    devicedict = await self._async_get_device(ip_info["address"], 8099)
                    ip_addr = ip_info.get("address")
                    break
                except:
                    ip_addr = "127.0.0.1"
                    continue

        if user_input is not None:
            try:
                devicedict = await self._async_get_device(
                    user_input[CONF_HOST], user_input[CONF_PORT]
                )
            except EcoPanelConnectionError:
                errors["base"] = "cannot_connect"
            except EcoPanelEmptyResponseError:
                errors["base"] = "empty_response"
            else:
                return self.async_create_entry(
                    title="BACnet Interface",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, description={"suggested_value": ip_addr}
                    ): str,
                    vol.Required(CONF_PORT, description={"suggested_value": 8099}): int,
                }
            ),
            errors=errors,
        )

    async def _async_get_device(self, host: str, port: int) -> DeviceDict:
        """Get device information from add-on."""
        session = async_get_clientsession(self.hass)
        interface = Interface(host=host, port=port, session=session)
        return await interface.update()


class OptionsFlowHandler(OptionsFlow):
    """Handle Options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage EcoPanel options."""
        errors = {}

        if user_input is not None:
            # Update config entry with data from user input

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(
                title=self.config_entry.title, data=user_input
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        description={
                            "suggested_value": self.config_entry.data.get(CONF_HOST)
                        },
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_PORT, 8099
                            )
                        },
                    ): int,
                }
            ),
        )
