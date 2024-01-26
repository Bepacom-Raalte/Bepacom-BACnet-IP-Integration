"""Constants for the Bepacom BACnet/IP integration."""
import logging
from datetime import timedelta

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "bacnet_interface"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(seconds=60)

STATETEXT_OFFSET = 1  # JCO
