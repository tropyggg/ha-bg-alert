import logging
import asyncio
from datetime import timedelta
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

DOMAIN = "bg_alert"
_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Създаване на сензорите на база избраните настройки."""
    region = entry.data.get("region", "Всички региони")
    scan_interval = entry.data.get("scan_interval", 30)
    scan_interval_td = timedelta(seconds=scan_interval)

    # Първите два сензора винаги се създават (те са регионални)
    entities = [
        BgAlertEmergencySensor(entry.entry_id, region, scan_interval_td),
        BgAlertNewsSensor(entry.entry_id, region, scan_interval_td)
    ]

    # ЛОГИКА: Ако НЕ е избрано "Всички региони", добавяме 3-тия сензор за общ архив
    if region != "Всички региони":
        entities.append(BgAlertAllNewsSensor(entry.entry_id, region, scan_interval_td))

    async_add_entities(entities, update_before_add=True)


class BgAlertEmergencySensor(SensorEntity):
    """Сензор 1: Регионални спешни сигнали за реални опасности."""
    def __init__(self, entry_id, region, scan_interval):
        self._entry_id = entry_id
        self._region = region
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Спешни сигнали"
        self._attr_unique_id = f"bg_alert_emergency_{region.lower().replace(' ', '_')}"
        
        self._state = "Няма активни опасности"
        self._attributes = {"регион": region, "съобщение": "Всичко е наред"}

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
                async with session.get(url, headers=HEADERS, timeout=10) as response:
                    if response.status != 200: return
                    xml_data = await response.text()

            soup = BeautifulSoup(xml_data, "xml")
            entries = soup.find_all("entry")
            
            if entries:
                latest_entry = entries[-1]
                title = latest_entry.find("title").text.strip() if latest_entry.find("title") else ""
                
                if self._region == "Всички региони" or self._region.lower() in title.lower():
                    self._state = "АКТИВНА ТРЕВОГА"
                    self._attributes["съобщение"] = title
                else:
                    self.reset()
            else:
                self.reset()
        except Exception as e:
            _LOGGER.error("Грешка при четене на спешни сигнали: %s", e)
            self.reset()

    def reset(self):
        self._state = "Няма активни опасности"
        self._attributes["съобщение"] = "Всичко е наред"


class BgAlertNewsSensor(SensorEntity):
    """Сензор 2: Регионални Новини и Тестове."""
    def __init__(self, entry_id, region, scan_interval):
        self._entry_id = entry_id
        self._region = region
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Новини и Тестове"
        self._attr_unique_id = f"bg_alert_news_{region.lower().replace(' ', '_')}"
        
        self._state = "Няма предстоящи тестове"
        self._attributes = {"регион": region, "информация": "Няма съобщения"}

    @property
    def state(self): return self._state

    @property
    def extra_state_attributes(self): return self._attributes

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    async def async_update(self):
        url = "https://bg-alert.bg"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS, timeout=10) as response:
                    if response.status != 200: return
                    xml_data = await response.text()

            soup = BeautifulSoup(xml_data, "xml")
            entries = soup.find_all("entry")
            
            if entries:
                regional_entries = []
                for entry in reversed(entries):
                    title = entry.find("title").text.strip() if entry.find("title") else ""
                    if self._region == "Всички региони" or self._region.lower() in title.lower():
                        regional_entries.append(title)
                
                if regional_entries:
                    latest_regional = regional_entries[0]
                    self._attributes["информация"] = latest_regional
                    if "тест" in latest_regional.lower() or "проверка" in latest_regional.lower():
                        self._state = "Планиран ТЕСТ"
                    else:
                        self._state = "Нова Новина"
                else:
                    self._state = "Няма предстоящи тестове"
                    self._attributes["информация"] = "Няма известия за този регион"
            else:
                self._state = "Няма нови анонси"
        except Exception as e:
            _LOGGER.error("Грешка при извличане на регионални новини: %s", e)


class BgAlertAllNewsSensor(SensorEntity):
    """Сензор 3: Пълен национален списък с изброени новини (Отпада при 'Всички региони')."""
    def __init__(self, entry_id, region, scan_interval):
        self._entry_id = entry_id
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Пълен архив новини"
        self._attr_unique_id = f"bg_alert_all_news_archive"
        
        self._state = 0
        self._attributes = {"целият_списък": []}

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
                async with session.get(url, headers=HEADERS, timeout=10) as response:
                    if response.status != 200: return
                    xml_data = await response.text()

            soup = BeautifulSoup(xml_data, "xml")
            entries = soup.find_all("entry")
            
            if entries:
                all_titles = []
                # Пълно изброяване на списъка от най-новите към най-старите
                for entry in reversed(entries):
                    title = entry.find("title").text.strip() if entry.find("title") else ""
                    if title:
                        all_titles.append(title)
                
                # Състоянието показва бройката на съобщенията в потока
                self._state = len(all_titles)
                self._attributes["целият_списък"] = all_titles
            else:
                self._state = 0
                self._attributes["целият_списък"] = []
        except Exception as e:
            _LOGGER.error("Грешка при извличане на националния архив: %s", e)
