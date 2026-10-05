import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

DOMAIN = "bg_alert"

REGIONS = [
    "Всички региони", "Благоевград", "Бургас", "Варна", "Велико Търново", 
    "Видин", "Враца", "Габрово", "Добрич", "Кърджали", "Кюстендил", 
    "Ловеч", "Монтана", "Пазарджик", "Перник", "Плевен", "Пловдив", 
    "Разград", "Русе", "Силистра", "Сливен", "Смолян", "София (град)", 
    "София (област)", "Стара Загора", "Търговище", "Хасково", "Шумен", "Ямбол"
]

class BgAlertConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Първоначално добавяне на интеграцията."""
    VERSION = 2

    def __init__(self):
        self.config_data = {}

    async def async_step_user(self, user_input=None):
        """Стъпка 1: Избор на хардуерен или софтуерен режим."""
        if user_input is not None:
            if user_input["mode"] == "hardware":
                # Показва съобщение за грешка / блок "В разработка"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({
                        vol.Required("mode", default="software"): vol.In({"software": "Софтуерен (Уеб емисии)", "hardware": "Хардуерен (Cell Broadcast Модем)"})
                    }),
                    errors={"base": "hardware_in_development"}
                )
            self.config_data["mode"] = "software"
            return await self.async_step_software_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("mode", default="software"): vol.In({"software": "Софтуерен (Уеб емисии)", "hardware": "Хардуерен (Cell Broadcast Модем)"})
            })
        )

    async def async_step_software_config(self, user_input=None):
        """Стъпка 2: Конфигуриране на софтуерния режим (филтри и време)."""
        if user_input is not None:
            self.config_data.update(user_input)
            return self.async_create_entry(title=f"BG-ALERT ({self.config_data['region']})", data=self.config_data)

        return self.async_show_form(
            step_id="software_config",
            data_schema=vol.Schema({
                vol.Required("region", default="Всички региони"): vol.In(REGIONS),
                vol.Required("scan_interval", default=30): vol.All(int, vol.Range(min=10, max=3600)),
            })
        )
