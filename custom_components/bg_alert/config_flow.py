import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

DOMAIN = "bg_alert"

MUNICIPALITIES = [
    "Всички общини",
    "Айтос", "Аксаково", "Алфатар", "Антон", "Антоново", "Априлци", "Асеновград",
    "Баните", "Банско", "Батак", "Белене", "Белица", "Белоградчик", "Белослав", "Берковица", "Благоевград", "Бобов дол", "Бобошево", "Божурище", "Бойница", "Бойчиновци", "Болярово",
    "Борино", "Борован", "Борово", "Ботевград", "Братя Даскалови", "Братя", "Брацигово", "Брегово", "Брезник", "Брезово", "Брусарци", "Бургас", "Бяла (Варна)", "Бяла (Русе)",
    "Бяла Слатина", "Варна", "Велики Преслав", "Велико Търново", "Велинград", "Венец", "Ветово", "Ветрино", "Видин", "Враца", "Вълчедръм", "Вълчи дол", "Върбица",
    "Вършец", "Габрово", "Генерал Тошево", "Георги Дамяново", "Главиница", "Годеч", "Горна Оряховица", "Гоце Делчев", "Грамада", "Гулянци", "Гурково", "Гълъбово",
    "Две могили", "Девин", "Девня", "Джебел", "Димитровград", "Димово", "Добрич", "Добрич-селска", "Долна баня", "Долна Митрополия", "Долни Чифлик", "Доспат", "Драгоман", "Дряново",
    "Дулово", "Дупница", "Дългопол", "Елена", "Елин Пелин", "Елхово", "Етрополе", "Завет", "Земен", "Златарица", "Златица", "Златоград", "Ивайловград", "Иваново", "Искър",
    "Исперих", "Каварна", "Казанлък", "Кайнарджа", "Калояново", "Камено", "Каолиново", "Карлово", "Карнобат", "Каспичан", "Кирково", "Кнежа", "Ковачевци", "Козлодуй", "Копривщица",
    "Костенец", "Костинброд", "Котел", "Кочериново", "Кресна", "Криводол", "Кричим", "Крумовград", "Крушари", "Кубрат", "Куклен", "Кула", "Кърджали", "Кюстендил",
    "Левски", "Лесичово", "Летница", "Ловеч", "Лозница", "Лом", "Луковит", "Лъки", "Любимец", "Мадан", "Маджарово", "Макреш", "Марица", "Медковец", "Мездра", "Мизия",
    "Минерални бани", "Мирково", "Момчилград", "Монтана", "Мъглиж", "Неделино", "Несебър", "Никола Козлево", "Николаево", "Никопол", "Нова Загора", "Нови пазар", "Ново село",
    "Омуртаг", "Опака", "Опан", "Оряхово", "Павел баня", "Павликени", "Пазарджик", "Панагюрище", "Перник", "Перущица", "Петрич", "Пещера", "Пирдоп", "Плевен", "Пловдив",
    "Полски Тръмбеш", "Поморие", "Попово", "Пордим", "Правец", "Приморско", "Провадия", "Раднево", "Радомир", "Разград", "Разлог", "Ракитово", "Раковски", "Рила", "Родопи", "Роман",
    "Рудозем", "Руен", "Русе", "Сатовча", "Садово", "Самоков", "Самуил", "Сандански", "Сапарева баня", "Свиленград", "Свищов", "Своге", "Севлиево", "Септември", "Силистра",
    "Симеоновград", "Симитли", "Ситово", "Сливен", "Сливница", "Сливо поле", "Смолян", "Смядово", "Созопол", "София (Столична)", "Средец", "Стамболийски", "Стамболово",
    "Стара Загора", "Стражица", "Стралджа", "Стрелча", "Струмяни", "Суворово", "Сухиндол", "Съединение", "Твърдица", "Тервел", "Тетевен", "Тополовград", "Троян", "Трън", "Трявна",
    "Тунджа", "Търговище", "Угърчин", "Хаджидимово", "Хайредин", "Харманли", "Хасково", "Хисаря", "Хитрино", "Цар Калоян", "Царево", "Ценово", "Чавдар", "Челопеч", "Чепеларе",
    "Червен бряг", "Черноочене", "Чипровци", "Чирпан", "Чупрене", "Шабла", "Шивачево", "Шумен", "Ябланица", "Якимово", "Якоруда", "Ямбол"
]

class BgAlertConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Мащабен двустъпков мениджър по новия архитектурен план."""
    VERSION = 3

    def __init__(self) -> None:
        super().__init__()
        self.config_data = {}

    async def async_step_user(self, user_input=None):
        """Стъпка 1: Потребителят избира точно какъв софтуерен или хардуерен модул иска."""
        errors = {}
        if user_input is not None:
            if user_input["mode"] == "hardware":
                errors["base"] = "hardware_in_development"
            elif user_input["mode"] == "archive":
                self.config_data = {"mode": "archive", "municipality": "Национален", "scan_interval": 60}
                return self.async_create_entry(title="BG-ALERT (Национален архив новини)", data=self.config_data)
            else:
                self.config_data["mode"] = "regional"
                return await self.async_step_software_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("mode", default="regional"): vol.In({
                    "regional": "Регионален сензор за опасности (Избор на община)",
                    "archive": "Национален списък и архив новини (Глобален)",
                    "hardware": "Хардуерен режим (Cell Broadcast радио модем)"
                })
            }),
            errors=errors
        )

    async def async_step_software_config(self, user_input=None):
        """Стъпка 2: Избор на град (Появява се САМО за регионалния режим)."""
        if user_input is not None:
            self.config_data.update(user_input)
            return self.async_create_entry(
                title=f"BG-ALERT ({self.config_data['municipality']})", 
                data=self.config_data
            )

        return self.async_show_form(
            step_id="software_config",
            data_schema=vol.Schema({
                vol.Required("municipality", default="Всички общини"): vol.In(MUNICIPALITIES),
                vol.Required("scan_interval", default=30): vol.All(int, vol.Range(min=10, max=3600)),
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BgAlertOptionsFlowHandler(config_entry)


class BgAlertOptionsFlowHandler(config_entries.OptionsFlow):
    """Промяна на настройките през бутона Configure."""
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        mode = self.config_entry.data.get("mode", "regional")
        if mode == "archive":
            return self.async_show_form(step_id="init", data_schema=vol.Schema({}))

        current_municipality = self.config_entry.options.get("municipality", self.config_entry.data.get("municipality", "Всички общини"))
        current_interval = self.config_entry.options.get("scan_interval", self.config_entry.data.get("scan_interval", 30))

        options_schema = vol.Schema({
            vol.Required("municipality", default=current_municipality): vol.In(MUNICIPALITIES),
            vol.Required("scan_interval", default=current_interval): vol.All(int, vol.Range(min=10, max=3600)),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)