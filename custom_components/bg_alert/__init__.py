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
    
    # Изтегляме автоматично преводите за секция "config" спрямо текущия език на HA
    translations = await hass.helpers.translation.async_get_translations(
        hass, hass.config.language, "config", [DOMAIN]
    )
    
    # Взимаме преведената дума (ако езикът няма превод, използваме "Municipality" като резерва)
    prefix = translations.get(f"component.{DOMAIN}.config.municipality_title", "Municipality")
    
    # Сглобяваме заглавието на екрана
    hass.config_entries.async_update_entry(entry, title=f"{prefix} {new_municipality}")
    
    await hass.config_entries.async_reload(entry.entry_id)
