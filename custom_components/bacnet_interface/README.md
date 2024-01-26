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

Copy this integration to your Home Assistant's 'custom_components' folder located in /config/.

If you don't know where this is located, follow this small explanation here. Through the 'Samba share' add-on, you can make this folder available on your network.

To add this on your Windows PC, go to "This PC", right click and select add networklocation, and then follow the wizard. 

Your home assistant address should be something like \\homeassistant.local\config.

When you got this done, create the 'custom_components' folder and paste the bacnet_interface integration folder there.

Restart Home Assistant after installing this integration.

Then, manually add this integration through Settings > Devices & Services > + Add Integration and search for "BACnet".

When the integration opens, you'll have to type an IP address and a port. 

Use 127.0.0.1 as IP for the least trouble. It's possible to use the hostname for the add-on as IP, i.e. 97683af0-bacnetinterface.

The port can be whichever port you set in the add-on, or if you don't want to open a port for it, 8099.

After this is done, congratulations! Your Bepacom EcoPanel BACnet Interface integration is installed!

If there is an error, be sure to check your supervisor logs.

Make sure the add-on is running. If there was a problem with the add-on, reload the integration after solving the issue.

