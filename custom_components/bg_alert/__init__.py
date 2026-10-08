import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "bg_alert"
PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Зареждане на интеграцията при стартиране."""
    hass.data.setdefault(DOMAIN, {})
    
    # Регистрация на слушател (Listener), който следи за натискане на бутона Configure
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
    """Автоматично рестартиране на сензорите, когато потребителят смени общината."""
    _LOGGER.info("Настройките на BG-ALERT бяха променени. Презареждане на сензорите...")
    await hass.config_entries.async_reload(entry.entry_id)
