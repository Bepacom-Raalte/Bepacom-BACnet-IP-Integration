"""DataUpdateCoordinator for EcoPanel."""
from __future__ import annotations

import asyncio
from datetime import timedelta

from aioecopanel import (DeviceDict, DeviceDictError, EcoPanelConnectionClosed,
                         EcoPanelError, Interface)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .const import DOMAIN, LOGGER, SCAN_INTERVAL


class EcoPanelDataUpdateCoordinator(DataUpdateCoordinator[DeviceDict]):
    """EcoPanel Data Update Coordinator"""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize EcoPanel data updater"""

        self.interface = Interface(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            session=async_get_clientsession(hass),
        )
        self.unsub: CALLBACK_TYPE | None = None

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        
    @callback
    def _use_websocket(self) -> None:
        """Use websockets for updating"""

        def check_data(data) -> None:
            LOGGER.debug("check_data")
            if not isinstance(data, DeviceDict):
                LOGGER.warning(f"Received data is not DeviceDict type! {data}")
            elif data.devices is None:
                LOGGER.warning(f"Received data.devices is NoneType!")
            else:
                LOGGER.debug(f"set updated data: {data.devices}")
                self.async_set_updated_data(data)

        async def listen() -> None:
            """Listen for state changes through websocket"""
            try:
                # Connect to websocket
                LOGGER.debug("Connecting websocket")
                await self.interface.connect()
            except EcoPanelError as e:
                self.logger.info(e)
                # If shutting down... shut down gracefully
                if self.unsub:
                    self.unsub()
                    self.unsub = None
                    LOGGER.debug(f"Unsub after failing to connect")
                return
            
            LOGGER.debug("Connected websocket")
            
            try:
                # This will stay running in the background.
                # It calls DataUpdateCoordinator.async_set_updated_data when a message is received on the websocket.
                # The data will then be accessable on coordinator.data where coordinator is the variable name of EcoPanelDataUpdateCoordinator.
                LOGGER.debug("Listening to websocket")
                await self.interface.listen(callback=check_data)

            except EcoPanelConnectionClosed as err:
                self.last_update_success = False
                self.logger.info(err)
            except EcoPanelError as err:
                self.last_update_success = False
                self.async_update_listeners()
                self.logger.error(err)
            except Exception as err:
                self.last_update_success = False
                self.async_update_listeners()
                self.logger.error(err)
            
            LOGGER.debug("Disconnecting websocket after listening")

            # Make sure we are disconnected
            await self.interface.disconnect()
            if self.unsub:
                self.unsub()
                self.unsub = None
                LOGGER.debug("Unsubbed")

        async def close_websocket(_: Event) -> None:
            """Close WebSocket connection."""
            LOGGER.debug("close_websocket")
            self.unsub = None
            if self.interface._client:
                LOGGER.debug("Has client")
            if self.interface.connect:
                LOGGER.debug("Is connected")
            await self.interface.disconnect()

        LOGGER.debug("Set unsub listener")

        # Clean disconnect WebSocket on Home Assistant shutdown
        self.unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, close_websocket
        )

        LOGGER.debug("Create listen task...")

        # Start listening
        self.config_entry.async_create_background_task(
            self.hass, listen(), "bacnet-listen"
        )

    async def _async_update_data(self) -> DeviceDict:
        try:
            LOGGER.debug("Async update data")
            devicedict = await self.interface.update(
                full_update=not self.last_update_success
            )
        except (EcoPanelError, DeviceDictError) as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error

        if devicedict is not None:
            LOGGER.debug(f"devicedict not None")

        if not self.interface.connect:
            LOGGER.debug(f"interface not connected yet")
            
        if not self.unsub:
            LOGGER.debug(f"No unsub yet")

        if devicedict is not None and not self.interface.connected and not self.unsub:
            LOGGER.debug("Use websocket")
            self._use_websocket()
            
        if self.last_update_success:
            LOGGER.debug(f"Last update was a success")

        LOGGER.debug(f"return devicedict: {devicedict.devices}")
        return devicedict
