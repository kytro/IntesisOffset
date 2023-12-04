from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from pyppeteer import launch
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES

DOMAIN = "intesis_offset"

class IntesisOffsetSensor(Entity):
    def __init__(self, device, username, password, url):
        self._name = device['name']
        self._entity_id = device['entity_id']
        self._state = None
        self._unique_id = device['entity_id']
        self._linked_entity_id = device['linked_entity_id']
        self._linked_entity_state = None
        
    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        @callback
        def update_state(event):
            """Update the state."""
            self._linked_entity_state = self.hass.states.get(self._linked_entity_id)

        # Listen for when linked_entity_id has a state change
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"entity_{self._linked_entity_id}_state_update", update_state
            )
        )

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def linked_sensor_state(self):
        """Return the state of the linked sensor."""
        return self._linked_entity_state.state if self._linked_entity_state else None
        
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # Get the configuration for this domain
    conf = hass.data[DOMAIN]

    # Create a sensor for each device
    sensors = []
    for device_name, device_config in conf[CONF_DEVICES].items():
        sensor = IntesisOffsetSensor(device_config, conf[CONF_USERNAME], conf[CONF_PASSWORD], conf[CONF_URL])
        sensors.append(sensor)

    async_add_entities(sensors, True)
