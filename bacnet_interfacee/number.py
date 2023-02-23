from collections.abc import Callable
from dataclasses import dataclass
from statistics import mode
from typing import Any

from homeassistant.components.number import (NumberDeviceClass, NumberEntity,
                                             NumberEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (DATA_BYTES, ELECTRIC_CURRENT_MILLIAMPERE,
                                 PERCENTAGE,
                                 SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                                 UnitOfTemperature,
                                 ELECTRIC_POTENTIAL_MILLIVOLT)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import DOMAIN, LOGGER
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
        for objectid in coordinator.data.devices[deviceid].objects:
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
        """Initialize a BACnet AnalogInput object as entity."""
        super().__init__(coordinator=coordinator)
        self.deviceid = deviceid
        self.objectid = objectid

    @property
    def unique_id(self) -> str:
        return f"{self.deviceid}_{self.objectid}"

    @property
    def name(self) -> str:
        return f"{self.coordinator.data.devices[self.deviceid].objects[self.objectid].objectName}"

    @property
    def icon(self):
        return "mdi:gesture-swipe-vertical"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def mode(self) -> str:
        return "box"

    @property
    def native_step(self):
        return 0.1

    @property
    def native_value(self):
        return (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue
        )

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
            return 100

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
            return -100

    @property
    def native_unit_of_measurement(self) -> str:
        if (
            self.device_class == NumberDeviceClass.TEMPERATURE
            and "celsius"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return UnitOfTemperature.CELSIUS
        else:
            return None

    @property
    def device_class(self) -> str:
        if (
            "degree"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return NumberDeviceClass.TEMPERATURE

        else:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "OutOfService": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .outOfService,
            "EventState": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .eventState,
            "reliability": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .reliability,
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
        await self.coordinator.interface.write_property(
            deviceid=self.deviceid, objectid=self.objectid, presentValue=value
        )


class AnalogValueEntity(CoordinatorEntity[EcoPanelDataUpdateCoordinator], NumberEntity):

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet AnalogInput object as entity."""
        super().__init__(coordinator=coordinator)
        self.deviceid = deviceid
        self.objectid = objectid

    @property
    def unique_id(self) -> str:
        return f"{self.deviceid}_{self.objectid}"

    @property
    def name(self) -> str:
        return f"{self.coordinator.data.devices[self.deviceid].objects[self.objectid].objectName}"

    @property
    def icon(self):
        return "mdi:pencil"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def mode(self) -> str:
        return "box"

    @property
    def native_step(self):
        return 0.1

    @property
    def native_value(self):
        return (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue
        )

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
            return 100

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
            return -100

    @property
    def native_unit_of_measurement(self) -> str:
        if (
            "celsius"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return UnitOfTemperature.CELSIUS
        elif(
            "percent"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
            ):
            return PERCENTAGE
        elif(
            "millivolt"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
            ):
            return ELECTRIC_POTENTIAL_MILLIVOLT
        else:
            return None

    @property
    def device_class(self) -> str:
        if (
            "degree"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return NumberDeviceClass.TEMPERATURE

        else:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "OutOfService": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .outOfService,
            "EventState": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .eventState,
            "reliability": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .reliability,
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
        await self.coordinator.interface.write_property(
            deviceid=self.deviceid, objectid=self.objectid, presentValue=value
        )
