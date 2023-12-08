import logging
import aiohttp
import asyncio
import voluptuous as vol

from bs4 import BeautifulSoup
from homeassistant.helpers import service
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES

DOMAIN = "intesis_offset"
_LOGGER = logging.getLogger(__name__)

# Define the service schema
SET_OFFSET_SCHEMA = vol.Schema({
    vol.Required('entity_id'): cv.entity_id,
    vol.Required('offset'): vol.All(vol.Coerce(int), vol.Clamp(min=-5, max=5))
})


class IntesisWeb:
    def __init__(self, base_url, username, password):
        self._base_url = base_url
        self._username = username
        self._password = password
        self._device_urls = None

    def get_device_urls(self, html, base_url):
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Find all devices
        devices = soup.find_all('li', class_='device bgDevice')

        # Extract the device names and their edit URLs
        device_urls = {}
        for device in devices:
            name = device.find('span', id=lambda x: x and x.endswith('_name')).text.strip()
            id = device['id'].replace('device_', '')
            url = f"{base_url}/device/edit?id={id}"
            device_urls[name] = url

        return device_urls
    
    def get_existing_offset(self, html):
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Find the select element for the temperature offset
        select = soup.find('select', id='vtempOffset')

        # Find the selected option
        selected_option = select.find('option', selected=True)

        # Extract and return the temperature offset from the option's text
        return int(selected_option.text.split(' ')[0])

    def get_device_id(self, device_name):
        # Check if the device name exists
        if device_name not in self._device_urls:
            print(f"No device named '{device_name}' found.")
            return None

        # Get the URL of the device
        url = self._device_urls[device_name]

        # Extract the device ID from the URL
        device_id = url.split('=')[1].split('&')[0]

        return device_id
            
    async def navigate_to_device_and_get_offset(self, s, device_name):
        # Check if the device name exists
        if device_name not in self._device_urls:
            print(f"No device named '{device_name}' found.")
            return None

        # Get the URL of the device
        url = self._device_urls[device_name]

        # Use the session instance to navigate to the device's edit URL
        response = await s.get(url)

        # Get the HTML of the page
        html = await response.text()
        
        # Get the existing temperature offset
        existing_offset = self.get_existing_offset(html)

        return existing_offset
    
    async def login(self, s):
        # Get the login page
        login_response = await s.get(self._base_url)
        login_html = await login_response.text()

        # Parse the HTML of the login page to find the CSRF token
        soup = BeautifulSoup(login_html, 'html.parser')
        csrf_token = soup.find('input', attrs={'name': 'signin[_csrf_token]'})['value']

        # Define the payload for post data
        payload = {
            'signin[username]': self._username,
            'signin[password]': self._password,
            'signin[_csrf_token]': csrf_token
        }

        # Post the payload to the site to log in
        p = await s.post(self._base_url, data=payload)

        # Extract the domain from the initial URL
        domain = self._base_url[:self._base_url.find("/", 8)]

        # Create the absolute URL
        settings_url = f"{domain}/device/list"

        # Follow the link and get the new page content
        settings_response = await s.get(settings_url)
        settings_page = await settings_response.text()

        # Get the device URLs
        self._device_urls = self.get_device_urls(settings_page, domain)
    
    async def async_get_offset(self, device_name):
        # Start a session
        s = aiohttp.ClientSession()
        await self.login(s)
        # Check if the device name exists
        if device_name not in self._device_urls:
            print(f"No device named '{device_name}' found.")
            return None
         
        offset = await self.navigate_to_device_and_get_offset(s, device_name)
        await s.close()
        return offset
      
    async def async_set_offset(self, device_name, offset):
        """Set the offset."""
        # Define the offset to value mapping based on the HTML
        offset_to_value = {
            -5: 65486,
            -4: 65496,
            -3: 65506,
            -2: 65516,
            -1: 65526,
             0: 0,
             1: 10,
             2: 20,
             3: 30,
             4: 40,
             5: 50
        }

        # Check if the offset is valid
        if offset not in offset_to_value:
            print(f"Invalid offset: {offset}. Offset must be between -5 and 5.")
            return

        # Get the corresponding value
        value = offset_to_value[offset]
        
        # Get the device ID
        device_id = await self.get_device_id(device_name)
        
        #uid - static
        uid = 50002
        
        #used_id - static for now
        used_id = 116771

        # Create the URL
        url = f"{self._base_url}/device/setVal?id={device_id}&uid={uid}&value={value}&userId={user_id}"

        # Define the headers
        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Cookie': 'cb-enabled=accepted; symfonyFrontend=h44kn87uih0p8jvhdpfsqbk735; shortscc=18',
            'DNT': '1',
            'Host': 'accloud.intesis.com',
            'Origin': 'https://accloud.intesis.com',
            'Referer': 'https://accloud.intesis.com/device/list',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        # Make the request
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                if response.status == 200:
                    return True
                else:
                    return False
        
        
class IntesisOffsetSensor(Entity):
    def __init__(self, hass, web, device):
        self._hass = hass
        self._name = device['name']
        self._entity_id = "intesis_" + device['entity_id']
        self._unique_id = "intesis_" + device['entity_id']
        self._linked_entity_id = device['linked_entity_id']
        self._intesisWeb = web

    async def async_init(self):
        self._state = await self._intesisWeb.async_get_offset(self._name)

    async def async_set_offset(self, offset):
        """Set the offset."""
        if isinstance(offset, int) and -5 <= offset <= 5:
            success = await self._intesisWeb.async_set_offset(self._name, offset)
            if success:
                self._state = offset
                return True
        return False

    @property
    def name(self):
        return self._name

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
    
    web = IntesisWeb(conf[CONF_URL], conf[CONF_USERNAME], conf[CONF_PASSWORD]);

    # Create a sensor for each device
    sensors = []
    for device_name, device_config in conf[CONF_DEVICES].items():
        sensor = IntesisOffsetSensor(hass, web, device_config)
        await sensor.async_init()
        sensors.append(sensor)

    async def async_handle_set_offset(call):
        """Handle the service call."""
        entity_id = call.data.get('entity_id')
        offset = call.data.get('offset')

        entity = next((sensor for sensor in sensors if sensor.entity_id == entity_id), None)

        if entity is not None and isinstance(entity, IntesisOffsetSensor):
            success = await entity.async_set_offset(offset)
            if not success:
                _LOGGER.error("Failed to set offset for %s", entity_id)
        else:
            _LOGGER.error("The entity %s is not an Intesis offset sensor", entity_id)

    hass.services.async_register(DOMAIN, 'set_offset', async_handle_set_offset, schema=SET_OFFSET_SCHEMA)
    
    async_add_entities(sensors, True)
