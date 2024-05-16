"""Config flow for Rako."""
from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class RakoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Rako config flow."""

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        data_schema = {
            vol.Required("ip"): str,
            vol.Required("username", default="admin"): str,
            vol.Required("password", default="microchip"): str,
        }
        return self.async_show_form(step_id="init", data_schema=vol.Schema(data_schema))
