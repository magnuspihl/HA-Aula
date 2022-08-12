from datetime import timedelta
import logging
from multiprocessing import AuthenticationError
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_GPS
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator
)
from .const import *
from .aula import AulaApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    config = hass.data[DOMAIN][entry.entry_id]
    coordinator = AulaCoordinator(hass, config[USERNAME], config[PASSWORD], config[ZONE])
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([AulaTracker(coordinator)])

class AulaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, username, password, zone):
        super().__init__(hass, _LOGGER, name="Aula", update_interval=timedelta(seconds=60))
        self.hass = hass
        self.username = username
        self.password = password
        self.zone = zone
    
    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(10):
                api = AulaApi(self.username, self.password)
                await self.hass.async_add_executor_job(api._login)
                overview = await self.hass.async_add_executor_job(api._get_daily_overview)
                return {
                    ATTR_NAME: overview[ATTR_NAME],
                    ATTR_STATUS: overview[ATTR_STATUS]
                }
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")

class AulaTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "aula_" + coordinator.data[ATTR_NAME]
    
    @property
    def source_type(self) -> str:
        return SOURCE_TYPE_GPS

    @property
    def latitude(self) -> float | None:
        return None
    
    @property
    def longitude(self) -> float | None:
        return None
    
    @property
    def location_name(self) -> str | None:
        if self.coordinator.data[ATTR_STATUS] == ATTR_STATUS_PRESENT:
            return self.coordinator.zone
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
    
    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        await self.coordinator.async_request_refresh()