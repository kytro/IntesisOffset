import logging
import aiohttp
import asyncio

from bs4 import BeautifulSoup
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES

DOMAIN = "intesis_offset"
_LOGGER = logging.getLogger(__name__)

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
            name = device.find('span', id=lambda x: x and x.endswith('_name')).text
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

    def get_device_id(device_name):
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
        
        await asyncio.sleep(2)
        
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
        
        
class IntesisOffsetSensor(Entity):
    def __init__(self, hass, web, device):
        self._hass = hass
        self._name = device['name']
        self._entity_id = device['entity_id']
        self._unique_id = device['entity_id']
        self._linked_entity_id = device['linked_entity_id']
        self._intesisWeb = web

    async def async_init(self):
        self._state = await self._intesisWeb.async_get_offset(self._name)

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

    async_add_entities(sensors, True)
