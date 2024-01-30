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

Firstly, install the Bepacom BACnet/IP add-on from here: 

[BACnet/IP-addon](https://github.com/Bepacom-Raalte/bepacom-HA-Addons/tree/main/bacnetinterface)

Download and copy this integration to your Home Assistant's 'custom_components' folder located in /config/.

If you don't know where this is located, follow this small explanation here. Through the 'Samba share' add-on, you can make this folder available on your network.

To add this on your Windows PC, go to "This PC", right click and select add networklocation, and then follow the wizard. 

Your home assistant address should be something like \\homeassistant.local\config.

When you got this done, create the 'custom_components' folder and paste the bacnet_interface integration folder there.

Restart Home Assistant after putting this integration in /config/.


# Configuration

Manually add this integration through Settings > Devices & Services > + Add Integration > "Bepacom BACnet/IP Interface".

When the configuration flow opens, you're greeted with a couple of options. These options are explaned below:

## IP Address

The IP address of the add-on. You can use an IP address or use the hostname of the add-on.
The integration tries to automatically set an IP for you, but if this fails, you can use "127.0.0.1" as address.
When using the hostname, you can write it as: "97683af0-bacnetinterface"

## Port

This is the port the integration will use for communication with the add-on.
The port can be whichever port you set in the add-on. If you set the port to blank in the add-on, use 8099 for this setting.
Port 8099 is always open in add-ons.

## Entity enabled by default

When setting up the integration for the first time, this setting will determine whether entities will be enabled by default or not.
If you want to adjust this after setting up the integration for the first time, you have to enable the entities by hand.

## Entity name based on

This setting will determine with what name an entity will appear in Home Assistant. There are 2 options which can be chosen from.
Option "Object name" will set the name to the object name property of the BACnet object.
Option "Description" will set the name to the description property of the BACnet object.


## Errors

If there is an error, be sure to check your supervisor logs.
Make sure the add-on is running. If there was a problem with the add-on, reload the integration after solving the issue.
If you think there's a bug or can't figure it out, feel free to contact the developers on [GitHub!](https://github.com/Bepacom-Raalte/bepacom-custom_components)