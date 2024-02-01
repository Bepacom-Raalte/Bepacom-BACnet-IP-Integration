"""The Bepacom EcoPanel BACnet/IP integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import (HomeAssistant, ServiceCall, ServiceResponse,
                                SupportsResponse)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry, async_get
from homeassistant.util.json import JsonObjectType

from .const import DOMAIN, LOGGER
from .coordinator import EcoPanelDataUpdateCoordinator

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS: list[str] = [
    "binary_sensor",
    "sensor",
    "number",
    "switch",
    "select",
]

WRITE_RELEASE_SERVICE_NAME = "write_release"
ATTR_PRIORITY = "priority"
WRITE_RELEASE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_PRIORITY): int,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoPanel BACnet/IP interface from a config entry."""

    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.

    coordinator = EcoPanelDataUpdateCoordinator(hass, entry=entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when its updated.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def write_release(call: ServiceCall) -> ServiceResponse:
        """Write empty presentValue that serves to release higher priority write request."""

        entity_registry = er.async_get(hass)

        entity_data = entity_registry.async_get(call.data[ATTR_ENTITY_ID][0])

        device_id, object_id = entity_data.unique_id.split("_")

        if call.data.get(ATTR_PRIORITY):
            LOGGER.warning("Priority is currently not functioning. Writing default value.")

        await coordinator.interface.write_property(
            deviceid=device_id, objectid=object_id
        )

        return {"status": "successfull!"}

    hass.services.async_register(
        DOMAIN,
        WRITE_RELEASE_SERVICE_NAME,
        write_release,
        schema=WRITE_RELEASE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: EcoPanelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

        await coordinator.interface.disconnect()
        if coordinator.unsub:
            coordinator.unsub()

        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove config entry from a device."""
    coordinator: EcoPanelDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    for domain, device_id in device_entry.identifiers:
        coordinator.logger.error(coordinator.data.devices[device_id])
        coordinator.data.devices.pop(device_id)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)
