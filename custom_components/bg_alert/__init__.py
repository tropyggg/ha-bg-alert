import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "bg_alert"
PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Зареждане на интеграцията при стартиране."""
    hass.data.setdefault(DOMAIN, {})
    
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Премахване на интеграцията (изчистване на сензорите без рестарт)."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Автоматично рестартиране на сензорите и обновяване на името на добавката на екрана."""
    _LOGGER.info("Настройките на BG-ALERT бяха променени. Презареждане...")
    
    new_municipality = entry.options.get("municipality", entry.data.get("municipality", "Всички общини"))
    
    hass.config_entries.async_update_entry(entry, title=new_municipality)
    
    await hass.config_entries.async_reload(entry.entry_id)
