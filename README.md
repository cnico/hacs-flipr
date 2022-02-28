# Flipr HACS

This project is obsolete since all the functionnalities it covers have been merged in the core distribution of HomeAssistant (cf : https://www.home-assistant.io/integrations/flipr/).
The source of this project is now in archive and should not be used.

To migrate to the official flipr integration, you should remove this custom hacs_flipr integration, restart homeassistant and then install the official flipr integration. If you have dashboards using flipr sensors, they should still work as most the sensor names did not changed. The only one that changed is date_measure renamed to last_measured.
