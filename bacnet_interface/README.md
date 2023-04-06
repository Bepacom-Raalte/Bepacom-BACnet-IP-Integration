# Bepacom EcoPanel BACnet Interface

This integration is intended to display the data from the Bepacom EcoPanel BACnet Interface add-on on the Lovelace UI of Home Assistant.

It currently supports these BACnet object types:

- Analog Input
- Analog Output
- Analog Value
- Binary Input
- Binary Output
- Binary Value
- Multi State Input
- Multi State Output
- Multi State Value



# Installation

First install the Bepacom BACnet/IP add-on from here: 

## [BACnet/IP-addon](https://github.com/Bepacom-Raalte/bepacom-HA-Addons/tree/main/bacnetinterface)

Copy this integration to your Home Assistant's 'custom_components' folder.

Then, manually add this integration through Settings > Devices & Services > + Add Integration and search for "BACnet".

When the integration opens, you'll have to type an IP address. Use 127.0.0.1, or any other IP address you know the BACnet add-on is running on.

After this is done, congratulations! Your Bepacom EcoPanel BACnet Interface integration is installed!

If there is an error, be sure to check your supervisor logs.

Make sure the add-on is running. If there was a problem with the add-on, reload the integration after solving the issue.

