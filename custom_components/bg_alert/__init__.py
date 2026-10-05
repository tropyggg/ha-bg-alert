import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "bg_alert"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Зареждане на интеграцията от менюто."""
    hass.data.setdefault(DOMAIN, {})
    
    # Слуша за промени в настройките (време за обновяване)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Препращане към създаването на сензора
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Премахване на интеграцията."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Презареждане при промяна на настройките."""
    await hass.config_entries.async_reload(entry.entry_id)
