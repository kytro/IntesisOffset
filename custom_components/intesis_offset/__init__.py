from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_URL, CONF_DEVICES
import voluptuous as vol

DOMAIN = "intesis_offset"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_URL): cv.url,
                vol.Required(CONF_DEVICES): vol.Schema(
                    {cv.entity_id: cv.string}
                ),
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
