"""Config flow for Hello World integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from aioecopanel import (DeviceDict, EcoPanelConnectionError,
                         EcoPanelEmptyResponseError, Interface)
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.config_entries import (CONN_CLASS_LOCAL_PUSH, ConfigEntry,
                                          ConfigFlow, ConfigFlowResult,
                                          OptionsFlow)
from homeassistant.const import (CONF_CUSTOMIZE, CONF_ENABLED, CONF_HOST,
                                 CONF_NAME, CONF_PORT, CONF_TARGET)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import selector
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

from .const import CONF_ANALOG_OUTPUT  # pylint:disable=unused-import
from .const import (CONF_ANALOG_VALUE, CONF_BINARY_OUTPUT, CONF_BINARY_VALUE,
                    CONF_MULTISTATE_OUTPUT, CONF_MULTISTATE_VALUE, DOMAIN,
                    LOGGER, NAME_OPTIONS, WRITE_OPTIONS)

_LOGGER = LOGGER


class EcoPanelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the EcoPanel."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Initialize options flow."""
        self.options = dict()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_import(self, import_info: dict[str, Any]) -> ConfigFlowResult:
        """Set the config entry up from yaml."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="BACnet Interface", data=import_info)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""

        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_host()

    async def _async_get_device(self, host: str, port: int) -> DeviceDict:
        """Get device information from add-on."""
        session = async_get_clientsession(self.hass)
        interface = Interface(host=host, port=port, session=session)
        return await interface.update()

    async def async_step_host(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get options for naming the entities"""

        errors = {}

        if user_input is not None:

            try:
                devicedict = await self._async_get_device(
                    host=user_input[CONF_HOST], port=user_input[CONF_PORT]
                )
            except EcoPanelConnectionError:
                errors["base"] = "cannot_connect"
            except EcoPanelEmptyResponseError:
                errors["base"] = "empty_response"
            else:
                self.options.update(user_input)
                return await self.async_step_naming()

        return self.async_show_form(
            step_id="host",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        description={"suggested_value": "127.0.0.1"},
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        description={
                            "suggested_value": self.options.get(CONF_PORT, 8099)
                        },
                    ): int,
                }
            ),
            errors=errors,
        )

    async def async_step_naming(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get options for naming the entities"""

        # Show form for naming and if you want to have advanced config. If so, option step_writing will be presented.

        if user_input is not None:
            self.options.update(user_input)

            if user_input[CONF_CUSTOMIZE]:
                return await self.async_step_writing()

            return await self._create_options()

        return self.async_show_form(
            step_id="naming",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        description={
                            "suggested_value": self.options.get(
                                CONF_NAME, "object_name"
                            )
                        },
                    ): selector(
                        {
                            "select": {
                                "options": NAME_OPTIONS,
                                "multiple": False,
                                "translation_key": "name_select",
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Required(
                        CONF_ENABLED, description={"suggested_value": True}
                    ): bool,
                    vol.Required(
                        CONF_CUSTOMIZE,
                        description={
                            "suggested_value": self.options.get(CONF_CUSTOMIZE, False)
                        },
                    ): bool,
                }
            ),
        )

    async def async_step_writing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get options for what properties to write to per objecttype"""

        if user_input is not None:
            self.options.update(user_input)
            return await self._create_options()

        write_selector = selector(
            {
                "select": {
                    "options": WRITE_OPTIONS,
                    "multiple": False,
                    "translation_key": "write_options",
                    "mode": "dropdown",
                }
            }
        )

        return self.async_show_form(
            step_id="writing",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ANALOG_OUTPUT,
                        description={
                            "suggested_value": self.options.get(
                                CONF_ANALOG_OUTPUT, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_ANALOG_VALUE,
                        description={
                            "suggested_value": self.options.get(
                                CONF_ANALOG_VALUE, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_BINARY_OUTPUT,
                        description={
                            "suggested_value": self.options.get(
                                CONF_BINARY_OUTPUT, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_BINARY_VALUE,
                        description={
                            "suggested_value": self.options.get(
                                CONF_BINARY_VALUE, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_MULTISTATE_OUTPUT,
                        description={
                            "suggested_value": self.options.get(
                                CONF_MULTISTATE_OUTPUT, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_MULTISTATE_VALUE,
                        description={
                            "suggested_value": self.options.get(
                                CONF_MULTISTATE_VALUE, "present_value"
                            )
                        },
                    ): write_selector,
                }
            ),
        )

    async def _create_options(self) -> ConfigFlowResult:
        """Update config entry options."""

        # self.hass.config_entries.async_update_entry(self.config_entry, data=self.options)

        return self.async_create_entry(title="BACnet Interface", data=self.options)


class OptionsFlowHandler(OptionsFlow):
    """Handle Options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage EcoPanel options."""

        return await self.async_step_host()

    async def _async_get_device(self, host: str, port: int) -> DeviceDict:
        """Get device information from add-on."""
        session = async_get_clientsession(self.hass)
        interface = Interface(host=host, port=port, session=session)
        return await interface.update()

    async def async_step_host(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get options for naming the entities"""

        errors = {}

        if user_input is not None:

            try:
                devicedict = await self._async_get_device(
                    host=user_input[CONF_HOST], port=user_input[CONF_PORT]
                )
            except EcoPanelConnectionError:
                errors["base"] = "cannot_connect"
            except EcoPanelEmptyResponseError:
                errors["base"] = "empty_response"
            else:
                self.options.update(user_input)
                return await self.async_step_naming()

        return self.async_show_form(
            step_id="host",
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
            errors=errors,
        )

    async def async_step_naming(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get options for naming the entities"""

        # Show form for naming and if you want to have advanced config. If so, option step_writing will be presented.

        if user_input is not None:
            self.options.update(user_input)

            if user_input[CONF_CUSTOMIZE]:
                return await self.async_step_writing()

            return await self._update_options()

        return self.async_show_form(
            step_id="naming",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_NAME, "object_name"
                            )
                        },
                    ): selector(
                        {
                            "select": {
                                "options": NAME_OPTIONS,
                                "multiple": False,
                                "translation_key": "name_select",
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Required(
                        CONF_CUSTOMIZE,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_CUSTOMIZE, False
                            )
                        },
                    ): bool,
                }
            ),
        )

    async def async_step_writing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get options for what properties to write to per objecttype"""
        # show form for analogValue, analogOutput, binaryValue, binaryOutput, multiStateValue, multiStateOutput with dropdown choosing either present_value or relinquishDefault

        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        write_selector = selector(
            {
                "select": {
                    "options": WRITE_OPTIONS,
                    "multiple": False,
                    "translation_key": "write_options",
                    "mode": "dropdown",
                }
            }
        )

        return self.async_show_form(
            step_id="writing",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ANALOG_OUTPUT,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_ANALOG_OUTPUT, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_ANALOG_VALUE,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_ANALOG_VALUE, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_BINARY_OUTPUT,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_BINARY_OUTPUT, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_BINARY_VALUE,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_BINARY_VALUE, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_MULTISTATE_OUTPUT,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_MULTISTATE_OUTPUT, "present_value"
                            )
                        },
                    ): write_selector,
                    vol.Required(
                        CONF_MULTISTATE_VALUE,
                        description={
                            "suggested_value": self.config_entry.data.get(
                                CONF_MULTISTATE_VALUE, "present_value"
                            )
                        },
                    ): write_selector,
                }
            ),
        )

    async def _update_options(self) -> ConfigFlowResult:
        """Update config entry options."""

        self.hass.config_entries.async_update_entry(
            self.config_entry, data=self.options
        )

        return self.async_create_entry(title=self.config_entry.title, data=self.options)
