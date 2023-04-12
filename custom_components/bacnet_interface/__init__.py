"""The Bepacom EcoPanel BACnet integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry, async_get

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
    # coordinator: EcoPanelDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # identifiers = device_entry.identifiers()

    # coordinator.logger.error()

    # coordinator.interface.websocket_write_property() Tell add-on to remove old device

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)
