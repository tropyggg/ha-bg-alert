import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.translation import async_get_translations

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
    
    # 1. Взимаме текущия език на системата (ако няма, слагаме английски по подразбиране)
    current_language = hass.config.language if hass.config.language else "en"

    # 2. Извикваме преводите от папка translations конкретно за категория "config" на bg_alert
    # Тъй като bg_alert е custom_component, тук се подава името на папката му
    translations = await async_get_translations(
        hass, 
        current_language, 
        "config", 
        ["bg_alert"]
    )

    # 3. Home Assistant сглобява вътрешен ключ за превода. 
    # Структурата му е: component.{domain}.config.{твой_ключ}
    # Заменяме "bg_alert" с твоя реальный DOMAIN, ако се казва по друг начин в кода
    translation_key = f"component.bg_alert.config.municipality_title"

    # 4. Взимаме преведената дума от речника. 
    # Ако нещо се обърка или липсва превод, слагаме "Municipality" като резервен вариант (fallback)
    translated_word = translations.get(translation_key, "Municipality")

    # 5. Обновяваме заглавието на интеграцията с динамично преведената дума
    hass.config_entries.async_update_entry(entry, title=f"{translated_word} {new_municipality}")

    await hass.config_entries.async_reload(entry.entry_id)