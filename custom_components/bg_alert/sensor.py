import logging
import asyncio
from datetime import timedelta
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

DOMAIN = "bg_alert"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Създаване на сензорите."""
    region = entry.data.get("region", "Всички региони")
    scan_interval = entry.data.get("scan_interval", 30)
    scan_interval_td = timedelta(seconds=scan_interval)

    alert_sensor = BgAlertEmergencySensor(entry.entry_id, region, scan_interval_td)
    news_sensor = BgAlertNewsSensor(entry.entry_id, region, scan_interval_td)

    async_add_entities([alert_sensor, news_sensor], update_before_add=True)

class BgAlertEmergencySensor(SensorEntity):
    """Сензор за реални извънредни опасности."""
    def __init__(self, entry_id, region, scan_interval):
        self._entry_id = entry_id
        self._region = region
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Спешни сигнали"
        self._attr_unique_id = f"bg_alert_emergency_{region.lower().replace(' ', '_')}"
        
        self._state = "Няма активни опасности"
        self._attributes = {"регион": region, "последно_заглавие": "Няма", "съдържание": "Няма"}

    @property
    def state(self): return self._state

    @property
    def extra_state_attributes(self): return self._attributes

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"BG-ALERT ({self._region})",
            manufacturer="Министерство на вътрешните работи",
        )

    async def async_update(self):
        url = "https://bg-alert.bg/bg-alert-ws/public/alerts/atom"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200: return
                    xml_data = await response.text()

            # Използваме BeautifulSoup с xml парсер, за да заобиколим счупени тагове
            soup = BeautifulSoup(xml_data, "xml")
            
            # Търсим както 'entry' (Atom), така и 'item' (RSS)
            item = soup.find("entry") or soup.find("item")
            
            if item:
                title = item.find("title").text.strip() if item.find("title") else ""
                summary = (item.find("summary") or item.find("description") or item.find("content")).text.strip() if (item.find("summary") or item.find("description") or item.find("content")) else ""
                
                if self._region == "Всички региони" or self._region.lower() in summary.lower() or self._region.lower() in title.lower():
                    self._state = "АКТИВНА ТРЕВОГА"
                    self._attributes["последно_заглавие"] = title
                    self._attributes["съдържание"] = summary
                else:
                    self.reset()
            else:
                self.reset()
        except Exception as e:
            _LOGGER.error("Грешка при четене на спешни сигнали: %s", e)
            self.reset()

    def reset(self):
        self._state = "Няма активни опасности"
        self._attributes["последно_заглавие"] = "Няма"
        self._attributes["съдържание"] = "Няма"


class BgAlertNewsSensor(SensorEntity):
    """Сензор за Новини и Бъдещи Тестове."""
    def __init__(self, entry_id, region, scan_interval):
        self._entry_id = entry_id
        self._region = region
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Новини и Тестове"
        self._attr_unique_id = f"bg_alert_news_{region.lower().replace(' ', '_')}"
        
        self._state = "Няма нови анонси"
        self._attributes = {"информация": "Няма активни съобщения"}

    @property
    def state(self): return self._state

    @property
    def extra_state_attributes(self): return self._attributes

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    async def async_update(self):
        url = "https://bg-alert.bg/bg-alert-ws/public/news/atom"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200: return
                    xml_data = await response.text()

            soup = BeautifulSoup(xml_data, "xml")
            item = soup.find("entry") or soup.find("item")
            
            if item:
                title = item.find("title").text.strip() if item.find("title") else ""
                summary = (item.find("summary") or item.find("description") or item.find("content")).text.strip() if (item.find("summary") or item.find("description") or item.find("content")) else ""
                
                if "тест" in title.lower() or "проверка" in title.lower() or "тест" in summary.lower():
                    self._state = "Планиран ТЕСТ"
                else:
                    self._state = "Нова Новина"
                    
                self._attributes["информация"] = f"{title}: {summary}"
            else:
                self._state = "Няма нови анонси"
        except Exception as e:
            _LOGGER.error("Грешка при извличане на новини: %s", e)
            self._state = "Няма нови анонси"
