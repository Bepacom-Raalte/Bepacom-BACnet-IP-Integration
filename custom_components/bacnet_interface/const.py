"""Constants for the Bepacom BACnet/IP integration."""

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "bacnet_interface"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=60)

STATETEXT_OFFSET = 1  # JCO

NAME_OPTIONS = ["object_name", "description", "object_identifier"]

WRITE_OPTIONS = ["presentValue", "relinquishDefault"]

WRITE_RELEASE_SERVICE_NAME = "write_release"
ATTR_PRIORITY = "priority"
WRITE_RELEASE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_PRIORITY): int,
    }
)

WRITE_PROPERTY_SERVICE_NAME = "write_property"
ATTR_PROPERTY = "property"
ATTR_VALUE = "value"
ATTR_INDEX = "array_index"
WRITE_PROPERTY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_PROPERTY): str,
        vol.Optional(ATTR_VALUE): str,
        vol.Optional(ATTR_INDEX): int,
        vol.Optional(ATTR_PRIORITY): int,
    }
)

CONF_ANALOG_OUTPUT = "analog_output"
CONF_ANALOG_VALUE = "analog_value"
CONF_BINARY_OUTPUT = "binary_output"
CONF_BINARY_VALUE = "binary_value"
CONF_MULTISTATE_OUTPUT = "multistate_output"
CONF_MULTISTATE_VALUE = "multistate_value"

CONST_COMPARE_SIZE = 60