from homeassistant.helpers.entity import Entity
from pyppeteer import launch
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL

DOMAIN = "intesis_offset"

class OffsetSensor(Entity):
    def __init__(self, hass):
        self.hass = hass
        self._state = 0
        self._attributes = {"offset_values": [0, 10, 20, 30, 40, 50]}
        self.browser = None

    @property
    def state(self):
        return self._state

    @property
    def state_attributes(self):
        return self._attributes
        
    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        # Launch the browser
        self.browser = await launch(headless=False)
        page = await self.browser.newPage()

        # Get the configuration from hass.data
        conf = self.hass.data[DOMAIN]

        # Get the username, password, and URL from the configuration
        username = conf[CONF_USERNAME]
        password = conf[CONF_PASSWORD]
        url = conf[CONF_URL]

        # Navigate to the login page
        await page.goto(url)

        # Enter the username and password
        await page.type('input[name="signin[username]"]', username)
        await page.type('input[name="signin[password]"]', password)

        # Click the submit button
        await page.click('input[type="submit"]')

        # Wait for navigation to complete
        await page.waitForNavigation()

        # Navigate to the next page
        await page.goto('https://accloud.intesis.com/device/list')

        # Perform the initial update
        await self.async_update(page)


    async def async_update(self, page):
        # Check if login has timed out
        if await page.evaluate('''() => !document.querySelector('ul.devices')'''):
            # If login has timed out, re-initiate the login process
            await self.login(page)

        # Get the device IDs
        device_ids = await page.evaluate('''() => Array.from(document.querySelectorAll('ul.devices li.device span[id^="device_"]')).map(device => device.id)''')

        # Initialize a dictionary to store the offsets for each device
        offsets = {}

        # For each device ID...
        for device_id in device_ids:
            # Click on the device name to navigate to the device page
            await page.click(f"span[id='{device_id}_name']")

            # Wait for the offset selector to be visible
            await page.waitForSelector("select#vtempOffset")

            # Get the current offset
            offset = await page.evaluate('''() => document.querySelector("select#vtempOffset").value''')

            # Store the offset in the dictionary
            offsets[device_id] = offset

            # Navigate back to the device list page
            await page.goto('https://accloud.intesis.com/device/list')

        # Close the browser
        await self.browser.close()

        # Update the state attributes with the offsets
        self._attributes = {"offsets": offsets}

    async def login(self, page):
        # Get the configuration from hass.data
        conf = self.hass.data[DOMAIN]

        # Get the username, password, and URL from the configuration
        username = conf[CONF_USERNAME]
        password = conf[CONF_PASSWORD]
        url = conf[CONF_URL]

        # Navigate to the login page
        await page.goto(url)

        # Enter the username and password
        await page.type('input[name="signin[username]"]', username)
        await page.type('input[name="signin[password]"]', password)

        # Click the submit button
        await page.click('input[type="submit"]')

        # Wait for navigation to complete
        await page.waitForNavigation()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
        """Set up the sensor platform."""
        async_add_entities([OffsetSensor(hass)])
