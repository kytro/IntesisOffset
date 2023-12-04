from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import logging
from pyppeteer import launch
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES

DOMAIN = "intesis_offset"
_LOGGER = logging.getLogger(__name__)

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
        await self.update(page)

    async def fetch_data(self, device_name):
        if self.page is None:
            await self.login()

        # Check if the page has the right elements
        element = await self.page.querySelector('ul.devices')
        if element is None:
            await self.login()
            
        # Get the device IDs
        device_ids = await page.evaluate('''() => Array.from(document.querySelectorAll('ul.devices li.device span[id^="device_"]')).map(device => device.id)''')
        
        # Click on the device name to navigate to the device page
        await page.click(f"span[id='{device_id}_name']")
        
        # Wait for the offset selector to be visible
        await page.waitForSelector("select#vtempOffset")

        # Fetch data from the website
        data = await page.evaluate('''() => document.querySelector("select#vtempOffset").value''')

        return data

class IntesisOffsetSensor(Entity):
    def __init__(self, device, fetcher):
        self._name = device['name']
        self._entity_id = device['entity_id']
        self._unique_id = device['entity_id']
        self._linked_entity_id = device['linked_entity_id']
        self._linked_entity_state = None
        self._fetcher = fetcher
        self._state = get_offset()
    
    def get_offset(self):
        self._state =  self._fetcher.fetch_data (self._name)
    
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
            'Linked Entity': self._linked_entity_id 
        }
        
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # Get the configuration for this domain
    conf = hass.data[DOMAIN]
    
    # Create a single WebFetcher for all devices
    fetcher = WebFetcher(conf[CONF_URL], conf[CONF_USERNAME], conf[CONF_PASSWORD])

    # Create a sensor for each device
    sensors = []
    for device_name, device_config in conf[CONF_DEVICES].items():
        sensor = IntesisOffsetSensor(device_config, fetcher)
        sensors.append(sensor)

    async_add_entities(sensors, True)
