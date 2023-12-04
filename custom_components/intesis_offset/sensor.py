from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from pyppeteer import launch
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES

DOMAIN = "intesis_offset"

class WebFetcher:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.page = None
        self.browser = None
        
    async def login(self):
        self.browser = await launch(headless=True)
        self.page = await self.browser.newPage()
        await self.page.goto(self.url)

        # Replace 'username_selector' and 'password_selector' with the actual selectors
        await self.page.type('input[name="signin[username]"]', username)
        await self.page.type('input[name="signin[password]"]', password)

        # Replace 'login_button_selector' with the actual selector
        await self.page.click('input[type="submit"]')
        await self.page.waitForNavigation()
        
        # Navigate to the next page
        await page.goto('https://accloud.intesis.com/device/list')

    async def fetch_data(self):
        if self.page is None:
            await self.login()

        # Check if the page has the right elements
        # Replace 'element_selector' with the actual selector
        element = await self.page.querySelector('element_selector')
        if element is None:
            await self.login()

        # Fetch data from the website
        # Replace 'data_selector' with the actual selector
        data = await self.page.querySelectorEval('data_selector', '(element) => element.textContent')

        return data

class IntesisOffsetSensor(Entity):
    def __init__(self, device, username, password, url):
        self._name = device['name']
        self._entity_id = device['entity_id']
        self._state = 0
        self._unique_id = device['entity_id']
        self._linked_entity_id = device['linked_entity_id']
        self._linked_entity_state = None
        self._fetcher = WebFetcher(url, username, password)
        
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
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            'test': 'ok'
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
