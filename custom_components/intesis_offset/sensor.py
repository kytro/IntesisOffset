from homeassistant.helpers.entity import Entity
from pyppeteer import launch
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL

DOMAIN = "intesis_offset"

class IntesisOffsetSensor(Entity):
    def __init__(self, device, username, password, url):
        self._name = device['name']
        self._entity_id = device['entity_id']
        self._state = None

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

    def update(self):
        self._state = self.client.get_device_data(self._entity_id)
