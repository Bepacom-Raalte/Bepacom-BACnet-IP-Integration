from collections.abc import Callable
from dataclasses import dataclass
from statistics import mode
from typing import Any

from homeassistant.components.number import (NumberDeviceClass, NumberEntity,
                                             NumberEntityDescription)
from homeassistant.components.number.const import DEVICE_CLASS_UNITS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_ENABLED, CONF_NAME, PERCENTAGE,
                                 UnitOfElectricCurrent,
                                 UnitOfElectricPotential, UnitOfInformation,
                                 UnitOfIrradiance, UnitOfTemperature)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import InvalidStateError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import CONF_ANALOG_OUTPUT, CONF_ANALOG_VALUE, DOMAIN, LOGGER
from .coordinator import EcoPanelDataUpdateCoordinator
from .helper import bacnet_to_device_class, bacnet_to_ha_units, key_to_property


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoPanel sensor based on a config entry."""
    coordinator: EcoPanelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity_list: list = []

    # Collect from all devices the objects that can become a sensor
    if not coordinator.data.devices:
        LOGGER.warning(f"No devices received from API!")
        return

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
                == "analogOutput"
            ):
                # Object Type to ObjectIdentifier[0]
                entity_list.append(
                    AnalogOutputEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )
            elif (
                coordinator.data.devices[deviceid].objects[objectid].objectIdentifier[0]
                == "analogValue"
            ):
                entity_list.append(
                    AnalogValueEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )

    async_add_entities(entity_list)


class AnalogOutputEntity(
    CoordinatorEntity[EcoPanelDataUpdateCoordinator], NumberEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet AnalogOutput object as entity."""
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
    def icon(self):
        return "mdi:gesture-swipe-vertical"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.coordinator.config_entry.data.get(CONF_ENABLED, False)

    @property
    def mode(self) -> str:
        return "box"

    @property
    def native_step(self):
        if (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .resolution
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .resolution
            )
        elif (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .covIncrement
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .covIncrement
            )
        else:
            return float(0.1)

    @property
    def native_value(self):
        value = self.coordinator.data.devices[self.deviceid].objects[self.objectid].presentValue
    
        if value is None:
            raise InvalidStateError
    
        value = float(value)
        return int(value) if self.native_step >= 1 else value

    @property
    def native_max_value(self):
        if (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .maxPresValue
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .maxPresValue
            )
        else:
            return 2147483647

    @property
    def native_min_value(self):
        if (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .minPresValue
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .minPresValue
            )
        else:
            return -2147483648

    @property
    def native_unit_of_measurement(self) -> str | None:
        if (
            units := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units
        ):
            return bacnet_to_ha_units(units)
        else:
            return None

    @property
    def device_class(self) -> str | None:
        if (
            units := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units
        ):
            return bacnet_to_device_class(units, DEVICE_CLASS_UNITS)
        else:
            return None

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

    async def async_set_native_value(self, value: float) -> None:
        """Set analogOutput object to active."""

        propertyid = self.coordinator.config_entry.data.get(
            CONF_ANALOG_OUTPUT, "present_value"
        )

        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=key_to_property(propertyid),
            value=value,
            array_index=None,
            priority=None,
        )


class AnalogValueEntity(CoordinatorEntity[EcoPanelDataUpdateCoordinator], NumberEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet AnalogValue object as entity."""
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
    def icon(self):
        return "mdi:pencil"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.coordinator.config_entry.data.get(CONF_ENABLED, False)

    @property
    def mode(self) -> str:
        return "box"

    @property
    def native_step(self):
        if (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .resolution
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .resolution
            )
        elif (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .covIncrement
        ):
            return float(
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .covIncrement
            )
        else:
            return float(0.1)

    @property
    def native_value(self):
        value = self.coordinator.data.devices[self.deviceid].objects[self.objectid].presentValue
    
        if value is None:
            raise InvalidStateError
    
        value = float(value)
        return int(value) if self.native_step >= 1 else value

    @property
    def native_max_value(self):
        if (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .maxPresValue
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .maxPresValue
            )
        else:
            return 2147483647

    @property
    def native_min_value(self):
        if (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .minPresValue
        ):
            return (
                self.coordinator.data.devices[self.deviceid]
                .objects[self.objectid]
                .minPresValue
            )
        else:
            return -2147483647

    @property
    def native_unit_of_measurement(self) -> str | None:
        if (
            units := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units
        ):
            return bacnet_to_ha_units(units)
        else:
            return None

    @property
    def device_class(self) -> str | None:
        if (
            units := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units
        ):
            return bacnet_to_device_class(units, DEVICE_CLASS_UNITS)
        else:
            return None

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

    async def async_set_native_value(self, value: float) -> None:
        """Set analogOutput object to active."""

        propertyid = self.coordinator.config_entry.data.get(
            CONF_ANALOG_VALUE, "present_value"
        )

        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=key_to_property(propertyid),
            value=value,
            array_index=None,
            priority=None,
        )
