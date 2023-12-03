from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES
import voluptuous as vol

DOMAIN = "intesis_offset"

DEVICE_SCHEMA = vol.Schema({
    vol.Required('name'): cv.string,
    vol.Required('linked_entity_id'): cv.entity_id,
    vol.Required('entity_id'): cv.string,
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_URL): cv.url,
                vol.Required(CONF_DEVICES): vol.Schema({cv.string: DEVICE_SCHEMA}),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass, config):
    # Get the configuration for this domain
    conf = config[DOMAIN]

    # Store the configuration in hass.data
    hass.data[DOMAIN] = conf

    # Load the sensor platform
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True
