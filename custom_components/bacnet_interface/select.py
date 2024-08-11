from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import (SelectEntity,
                                             SelectEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENABLED, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import STATETEXT_OFFSET  # JCO
from .const import (CONF_MULTISTATE_OUTPUT, CONF_MULTISTATE_VALUE, DOMAIN,
                    LOGGER)
from .coordinator import EcoPanelDataUpdateCoordinator
from .helper import key_to_property


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EcoPanel sensor based on a config entry."""
    coordinator: EcoPanelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity_list: list = []

    # Collect from all devices the objects that can become a select.
    for deviceid in coordinator.data.devices:
        if deviceid is None:
            LOGGER.warning(f"Device ID is None!")
            continue

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
                == "multiStateValue"
            ):
                if (
                    coordinator.data.devices[deviceid].objects[objectid].numberOfStates
                    < 1
                ):
                    LOGGER.warning(
                        f"{deviceid} {objectid} is invalid as it has less that 1 state."
                    )
                    continue

                entity_list.append(
                    MultiStateValueEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )
            elif (
                coordinator.data.devices[deviceid].objects[objectid].objectIdentifier[0]
                == "multiStateOutput"
            ):
                if (
                    coordinator.data.devices[deviceid].objects[objectid].numberOfStates
                    < 1
                ):
                    LOGGER.warning(
                        f"{deviceid} {objectid} is invalid as it has less that 1 state."
                    )
                    continue

                entity_list.append(
                    MultiStateOutputEntity(
                        coordinator=coordinator, deviceid=deviceid, objectid=objectid
                    )
                )

    async_add_entities(entity_list)


class MultiStateOutputEntity(
    CoordinatorEntity[EcoPanelDataUpdateCoordinator], SelectEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet MultiStateOutput object as entity."""
        super().__init__(coordinator=coordinator)
        self.deviceid = deviceid
        self.objectid = objectid

    @property
    def unique_id(self) -> str:
        return f"{self.deviceid}_{self.objectid}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.coordinator.config_entry.data.get(CONF_ENABLED, False)

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
        return "mdi:menu"

    @property
    def options(self) -> list:
        if (
            state_text := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .stateText
        ):
            if any(state_text):
                return state_text

        if (
            number_of_states := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .numberOfStates
        ):
            return [str(i) for i in range(1, number_of_states + 1)]

        else:
            LOGGER.error(
                f"{self.deviceid} {self.objectid} is missing REQUIRED numberOfStates property!"
            )
            return []

    @property
    def current_option(self) -> str:
        pres_val = int(
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue
        )

        if (
            state_text := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .stateText
        ):
            if any(state_text):
                return state_text[pres_val - STATETEXT_OFFSET]
        if (
            number_of_states := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .numberOfStates
        ):
            options = [str(i) for i in range(1, number_of_states + 1)]
            return options[pres_val - STATETEXT_OFFSET]
        else:
            return str(pres_val)

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

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""

        pres_val = self.options.index(option) + STATETEXT_OFFSET

        propertyid = self.coordinator.config_entry.data.get(
            CONF_MULTISTATE_OUTPUT, "present_value"
        )

        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=key_to_property(propertyid),
            value=pres_val,
            array_index=None,
            priority=None,
        )


class MultiStateValueEntity(
    CoordinatorEntity[EcoPanelDataUpdateCoordinator], SelectEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcoPanelDataUpdateCoordinator,
        deviceid: str,
        objectid: str,
    ):
        """Initialize a BACnet MultiStateValue object as entity."""
        super().__init__(coordinator=coordinator)
        self.deviceid = deviceid
        self.objectid = objectid

    @property
    def unique_id(self) -> str:
        return f"{self.deviceid}_{self.objectid}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.coordinator.config_entry.data.get(CONF_ENABLED, False)

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
        return "mdi:menu"

    @property
    def options(self) -> list:
        if (
            state_text := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .stateText
        ):
            if any(state_text):
                return state_text

        if (
            number_of_states := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .numberOfStates
        ):
            return [str(i) for i in range(1, number_of_states + 1)]

        else:
            LOGGER.error(
                f"{self.deviceid} {self.objectid} is missing REQUIRED numberOfStates property!"
            )
            return []

    @property
    def current_option(self) -> str:
        pres_val = int(
            self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .presentValue
        )

        if (
            state_text := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .stateText
        ):
            if any(state_text):
                return state_text[pres_val - STATETEXT_OFFSET]
        if (
            number_of_states := self.coordinator.data.devices[self.deviceid]
            .objects[self.objectid]
            .numberOfStates
        ):
            options = [str(i) for i in range(1, number_of_states + 1)]
            return options[pres_val - STATETEXT_OFFSET]
        else:
            return str(pres_val)

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

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""

        pres_val = self.options.index(option) + STATETEXT_OFFSET

        propertyid = self.coordinator.config_entry.data.get(
            CONF_MULTISTATE_VALUE, "present_value"
        )

        await self.coordinator.interface.write_property_v2(
            deviceid=self.deviceid,
            objectid=self.objectid,
            propertyid=key_to_property(propertyid),
            value=pres_val,
            array_index=None,
            priority=None,
        )
