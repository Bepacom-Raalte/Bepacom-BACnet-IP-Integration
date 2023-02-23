from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (TEMP_CELSIUS, PERCENTAGE, IRRADIATION_WATTS_PER_SQUARE_METER,
                                 UnitOfIrradiance, UnitOfTemperature)
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
                == "analogInput"
            ):
                entity_list.append(
                    AnalogInputEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )
            # elif coordinator.data.devices[deviceid].objects[objectid].objectType == 'accumulator':
            #    entity_list.append(AnalogInputEntity(coordinator=coordinator, deviceid=deviceid, objectid=objectid))
            # elif coordinator.data.devices[deviceid].objects[objectid].objectType == 'averaging':
            #    entity_list.append(AveragingEntity(coordinator=coordinator, deviceid=deviceid, objectid=objectid))
            elif (
                coordinator.data.devices[deviceid].objects[objectid].objectIdentifier[0]
                == "multiStateInput"
            ):
                entity_list.append(
                    MultiStateInputEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )

    async_add_entities(entity_list)


class AnalogInputEntity(CoordinatorEntity[EcoPanelDataUpdateCoordinator], SensorEntity):

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
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def native_value(self):
        return round(
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue,
            1,
        )

    @property
    def icon(self):
        return "mdi:gauge"

    @property
    def device_class(self) -> str:
        if (
            "degree"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return SensorDeviceClass.TEMPERATURE
        elif (
            "watts"
            and "meter"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return SensorDeviceClass.IRRADIANCE
        elif (
            "humidity"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return SensorDeviceClass.HUMIDITY
        else:
            return None

    @property
    def native_unit_of_measurement(self) -> str:
        if (
            self.device_class == SensorDeviceClass.TEMPERATURE
            and "celsius"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return TEMP_CELSIUS
        elif self.device_class == SensorDeviceClass.IRRADIANCE:
            return IRRADIATION_WATTS_PER_SQUARE_METER
        elif (
            self.device_class == SensorDeviceClass.HUMIDITY
            or "percent"
            in self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .units.lower()
        ):
            return PERCENTAGE

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

    @property
    def state_class(self) -> str:
        return "measurement"


class MultiStateInputEntity(
    CoordinatorEntity[EcoPanelDataUpdateCoordinator], SensorEntity
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
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def native_value(self):
        state_val = (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue
        )
        return (
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .stateText[state_val]
        )

    @property
    def icon(self):
        return "mdi:menu"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "OutOfService": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .outOfService,
            "EventState": self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .eventState,
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
