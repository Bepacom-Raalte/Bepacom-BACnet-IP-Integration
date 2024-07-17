from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (SwitchDeviceClass, SwitchEntity,
                                             SwitchEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENABLED, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import CONF_BINARY_OUTPUT, CONF_BINARY_VALUE, DOMAIN, LOGGER
from .coordinator import EcoPanelDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoPanel sensor based on a config entry."""
    coordinator: EcoPanelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity_list: list = []

    # Collect from all devices the objects that can become a sensor
    for deviceid in coordinator.data.devices:
        if not coordinator.data.devices[deviceid].objects:
            LOGGER.warning(f"No objects in {deviceid}!")
            continue

        for objectid in coordinator.data.devices[deviceid].objects:
            if (
                not coordinator.data.devices[deviceid]
                .objects[objectid]
                .objectIdentifier
            ):
                LOGGER.warning(f"No object identifier for {objectid} in {deviceid}!")
                continue

            if (
                coordinator.data.devices[deviceid].objects[objectid].objectIdentifier[0]
                == "binaryValue"
            ):
                entity_list.append(
                    BinaryValueEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )
            elif (
                coordinator.data.devices[deviceid].objects[objectid].objectIdentifier[0]
                == "binaryOutput"
            ):
                entity_list.append(
                    BinaryOutputEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )
    async_add_entities(entity_list)


class BinaryValueEntity(CoordinatorEntity[EcoPanelDataUpdateCoordinator], SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet BinaryValue object as entity."""
        super().__init__(coordinator=coordinator)
        self.deviceid = deviceid
        self.objectid = objectid

    @property
    def unique_id(self) -> str:
        return f"{self.deviceid}_{self.objectid}"

    @property
    def name(self) -> str:
        name = self.coordinator.config_entry.data.get(CONF_NAME, "object_name")
        if name == "description":
            return f"{self.coordinator.data.devices[self.deviceid].objects[self.objectid].description}"
        elif name == "object_identifier":
            identifier = (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .objectIdentifier
            )
            return f"{identifier[0]}:{identifier[1]}"
        else:
            return f"{self.coordinator.data.devices[self.deviceid].objects[self.objectid].objectName}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.coordinator.config_entry.data.get(CONF_ENABLED, False)

    @property
    def is_on(self) -> bool:
        pres_val = self.coordinator.data.devices[self.deviceid].objects[self.objectid].presentValue
        
        if isinstance(pres_val, str):
            return pres_val in {"active", "1"}
        elif isinstance(pres_val, int):
            return pres_val == 1
        elif isinstance(pres_val, bool):
            return pres_val
        else:
            self.coordinator.logger.debug(f"Unknown type for: {self.objectid} {self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue}")

    @property
    def icon(self):
        return "mdi:lightbulb-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.deviceid)},
            name=f"{self.coordinator.data.devices[self.deviceid].objects[self.deviceid].objectName}",
            manufacturer=self.coordinator.data.devices[self.deviceid]
            .objects[self.deviceid]
            .vendorName,
            model=self.coordinator.data.devices[self.deviceid]
            .objects[self.deviceid]
            .modelName,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "inAlarm": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[0]
            ),
            "fault": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[1]
            ),
            "overridden": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[2]
            ),
            "outOfService": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[3]
            ),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set BinaryValue object to active"""
        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=self.coordinator.config_entry.data.get(
                CONF_BINARY_VALUE, "presentValue"
            ),
            value=1,
            array_index=None,
            priority=None,
        )

    async def async_turn_off(self):
        """Set BinaryValue object to active."""
        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=self.coordinator.config_entry.data.get(
                CONF_BINARY_VALUE, "presentValue"
            ),
            value=0,
            array_index=None,
            priority=None,
        )


class BinaryOutputEntity(
    CoordinatorEntity[EcoPanelDataUpdateCoordinator], SwitchEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet BinaryOutput object as entity."""
        super().__init__(coordinator=coordinator)
        self.deviceid = deviceid
        self.objectid = objectid

    @property
    def unique_id(self) -> str:
        return f"{self.deviceid}_{self.objectid}"

    @property
    def name(self) -> str:
        name = self.coordinator.config_entry.data.get(CONF_NAME, "object_name")
        if name == "description":
            return f"{self.coordinator.data.devices[self.deviceid].objects[self.objectid].description}"
        elif name == "object_identifier":
            identifier = (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .objectIdentifier
            )
            return f"{identifier[0]}:{identifier[1]}"
        else:
            return f"{self.coordinator.data.devices[self.deviceid].objects[self.objectid].objectName}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.coordinator.config_entry.data.get(CONF_ENABLED, False)

    @property
    def is_on(self) -> bool:
        
        pres_val = self.coordinator.data.devices[self.deviceid].objects[self.objectid].presentValue
        
        if isinstance(pres_val, str):
            return pres_val in {"active", "1"}
        elif isinstance(pres_val, int):
            return pres_val == 1
        elif isinstance(pres_val, bool):
            return pres_val
        else:
            self.coordinator.logger.debug(f"Unknown type for: {self.objectid} {self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue}")

    @property
    def icon(self):
        return "mdi:lightbulb-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.deviceid)},
            name=f"{self.coordinator.data.devices[self.deviceid].objects[self.deviceid].objectName}",
            manufacturer=self.coordinator.data.devices[self.deviceid]
            .objects[self.deviceid]
            .vendorName,
            model=self.coordinator.data.devices[self.deviceid]
            .objects[self.deviceid]
            .modelName,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "inAlarm": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[0]
            ),
            "fault": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[1]
            ),
            "overridden": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[2]
            ),
            "outOfService": bool(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .statusFlags[3]
            ),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set BinaryOutput object to active"""
        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=self.coordinator.config_entry.data.get(
                CONF_BINARY_OUTPUT, "presentValue"
            ),
            value=1,
            array_index=None,
            priority=None,
        )

    async def async_turn_off(self):
        """Set BinaryOutput object to active."""
        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=self.coordinator.config_entry.data.get(
                CONF_BINARY_OUTPUT, "presentValue"
            ),
            value=0,
            array_index=None,
            priority=None,
        )
