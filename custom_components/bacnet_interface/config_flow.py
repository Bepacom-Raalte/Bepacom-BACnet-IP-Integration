"""Config flow for Hello World integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from aioecopanel import DeviceDict, EcoPanelConnectionError, Interface
from homeassistant.components import onboarding, zeroconf, dhcp
from homeassistant.config_entries import (CONN_CLASS_LOCAL_PUSH, ConfigEntry,
                                          ConfigFlow, OptionsFlow)
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession


from .const import DOMAIN, LOGGER  # pylint:disable=unused-import


_LOGGER = LOGGER


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the EcoPanel."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry: ConfigEntry) -> EcoPanelOptionsFlowHandler:
    #    """Get the options flow for this handler."""
    #    return EcoPanelOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            try:
                devicedict = await self._async_get_device(user_input[CONF_HOST])
            except EcoPanelConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="BACnet Interface",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                    },
                )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors or {},
        )

    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        logging.info(self.discovered_url)
        logging.info(discovery_info.macaddress)

    async def async_step_hassio(self, discovery_info: dict[str, Any]) -> FlowResult:
        """Prepare configuration for a Hass.io AdGuard Home add-on.
        This flow is triggered by the discovery component.
        """
        logging.info(discovery_info)
        self._hassio_discovery = discovery_info

    async def _async_get_device(self, host: str) -> DeviceDict:
        """Get device information from WLED device."""
        session = async_get_clientsession(self.hass)
        interface = Interface(host, session=session)
        return await interface.update()


# class EcoPanelOptionsFlowHandler(OptionsFlow):
#    """Handle WLED options."""

#    def __init__(self, config_entry: ConfigEntry) -> None:
#        """Initialize WLED options flow."""
#        self.config_entry = config_entry

#    async def async_step_init(
#        self, user_input: dict[str, Any] | None = None
#    ) -> FlowResult:
#        """Manage EcoPanel options."""
#        if user_input is not None:
#            return self.async_create_entry(title="", data=user_input)

#        return self.async_show_form(
#            step_id="user",
#            data_schema=vol.Schema(
#                {
#                    vol.Required(CONF_HOST):str
#                    }
#                ),
#        )
