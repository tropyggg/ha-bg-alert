import logging
import asyncio
from datetime import timedelta
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

DOMAIN = "bg_alert"
_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Създаване на трите сензора на база избраната община."""
    # ПРАВИЛНО: Вече взимаме municipality от настройките (със застраховка, ако липсва)
    municipality = entry.data.get("municipality", entry.options.get("municipality", "Всички общини"))
    scan_interval = entry.data.get("scan_interval", 30)
    scan_interval_td = timedelta(seconds=scan_interval)

    entities = [
        BgAlertEmergencySensor(entry.entry_id, municipality, scan_interval_td),
        BgAlertNewsSensor(entry.entry_id, municipality, scan_interval_td),
        BgAlertAllNewsSensor(entry.entry_id, municipality, scan_interval_td)
    ]

    async_add_entities(entities, update_before_add=True)


class BgAlertEmergencySensor(SensorEntity):
    """Сензор 1: Регионални спешни сигнали за реални опасности."""
    def __init__(self, entry_id, municipality, scan_interval):
        self._entry_id = entry_id
        self._municipality = municipality
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Спешни сигнали"
        self._attr_unique_id = f"bg_alert_emergency_{municipality.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
        
        self._state = "Няма активни опасности"
        self._attributes = {"община": municipality, "съобщение": "Всичко е наред"}

    @property
    def state(self): return self._state

    @property
    def extra_state_attributes(self): return self._attributes

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"BG-ALERT ({self._municipality})",
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
                
                # Филтриране по община
                if self._municipality == "Всички общини" or self._municipality.lower() in title.lower():
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
        self._state = "Няма active опасности" if self._state == "АКТИВНА ТРЕВОГА" else "Няма активни опасности"
        self._state = "Няма активни опасности"
        self._attributes["съобщение"] = "Всичко е наред"


class BgAlertNewsSensor(SensorEntity):
    """Сензор 2: Регионални Новини и Тестове (Само за ДНЕШНИ събития)."""
    def __init__(self, entry_id, municipality, scan_interval):
        self._entry_id = entry_id
        self._municipality = municipality
        self._scan_interval = scan_interval
        self._attr_has_entity_name = True
        self._attr_name = "Новини и Тестове"
        self._attr_unique_id = f"bg_alert_news_{municipality.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
        
        self._state = "Няма днешни тестове"
        self._attributes = {"община": municipality, "информация": "Няма днешни известия"}

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
                now = dt_util.now()
                today_alert_found = False

                for entry in reversed(entries):
                    title = entry.find("title").text.strip() if entry.find("title") else ""
                    pub_date_str = entry.find("published").text.strip() if entry.find("published") else ""
                    
                    if pub_date_str:
                        pub_date = dt_util.parse_datetime(pub_date_str)
                        
                        # Проверка за събития от последните 24 часа
                        if pub_date and (now - pub_date) < timedelta(days=1):
                            # Прецизен регионален филтър по име на община
                            if self._municipality == "Всички общини" or self._municipality.lower() in title.lower():
                                today_alert_found = True
                                self._attributes["информация"] = title
                                
                                if "тест" in title.lower() or "проверка" in title.lower():
                                    self._state = "Планиран ТЕСТ ДНЕС"
                                else:
                                    self._state = "Нова Новина ДНЕС"
                                break

                if not today_alert_found:
                    self._state = "Няма днешни тестове"
                    self._attributes["информация"] = "Всички съобщения в архива са стари."
            else:
                self._state = "Няма нови анонси"
        except Exception as e:
            _LOGGER.error("Грешка при извличане на регионални новини: %s", e)


class BgAlertAllNewsSensor(SensorEntity):
    """Сензор 3: Пълен национален архив с изброени новини."""
    def __init__(self, entry_id, municipality, scan_interval):
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
                for entry in reversed(entries):
                    title = entry.find("title").text.strip() if entry.find("title") else ""
                    if title:
                        all_titles.append(title)
                
                self._state = len(all_titles)
                self._attributes["целият_списък"] = all_titles
            else:
                self._state = 0
                self._attributes["целият_списък"] = []
        except Exception as e:
            _LOGGER.error("Грешка при извличане на националния архив: %s", e)