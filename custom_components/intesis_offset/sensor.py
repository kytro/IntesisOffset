from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
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
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            'linked_sensor_state': self.linked_sensor_state
        }
        
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
