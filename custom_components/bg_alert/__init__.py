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
    
    # Резервна дума по подразбиране
    prefix = "Municipality"
    
    try:
        # Взимаме текущия език на Home Assistant (напр. "bg", "en", "de")
        lang = hass.config.language
        
        # Намираме пътя до папката на нашата интеграция
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, "translations", f"{lang}.json")
        
        # Ако файлът за този език не съществува, използваме strings.json като шаблон
        if not os.path.exists(json_path):
            json_path = os.path.join(current_dir, "strings.json")
            
        # Отваряме и прочитаме файла директно от диска
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Изваждаме думата директно от структурата на JSON файла
            prefix = data["config"]["step"]["software_config"]["municipality_title"]
    except Exception as e:
        _LOGGER.warning("Неуспешно извличане на превод от JSON файла: %s", e)
        prefix = "Municipality"
    
    # Сглобяваме заглавието на екрана с реално прочетения превод
    hass.config_entries.async_update_entry(entry, title=f"{prefix} {new_municipality}")

    await hass.config_entries.async_reload(entry.entry_id)