import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *

class AulaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return AulaOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        schema = vol.Schema({
            vol.Required(USERNAME): str,
            vol.Required(PASSWORD): str,
            vol.Required(ZONE): str
        })

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)
        
        return self.async_create_entry(
            title="Aula (" + user_input[USERNAME] + ")",
            data={
                USERNAME: user_input[USERNAME],
                PASSWORD: user_input[PASSWORD],
                ZONE: user_input[ZONE]
            }
        )

class AulaOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
    
    async def async_step_init(self, user_input):
        if user_input is not None:
            return self.async_create_entry(title="Aula (" + user_input[USERNAME] + ")",
                data={
                    USERNAME: user_input[USERNAME],
                    PASSWORD: user_input[PASSWORD],
                    ZONE: user_input[ZONE]
                })

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(USERNAME): str,
                vol.Required(PASSWORD): str,
                vol.Required(ZONE): str
            })
        )