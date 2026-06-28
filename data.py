# -*- coding: utf-8 -*-

KURBANIA_ZONES = {
    "southwest_close": {"region": "Форская область", "depth": "close", "direction": "юго-запад", "places": ["Гона", "Зурба", "Черный", "Фрода", "Сейла", "Фор", "Шорок", "Велико-Умуртск"]},
    "west_close": {"region": "Моноройская область", "depth": "close", "direction": "запад", "places": ["Стрекозное", "Ройск", "Чопла", "Эниа", "Решедэн", "Агда", "Наржа", "Зеленостопль"]},
    "northwest_close": {"region": "Алугданская область", "depth": "close", "direction": "северо-запад", "places": ["Дерево", "Малая Зелень", "Дамир", "Нелель", "Жаднач"]},
    "north_close": {"region": "Сугданская область", "depth": "close", "direction": "север", "places": ["Сокол", "Велена", "Доковы"]},

    "southwest_middle": {"region": "Форская область", "depth": "middle", "direction": "юго-запад", "places": ["Вейла", "Ал", "Гоный Ал", "Евгено-Форов", "Малый Фор", "Кужда"]},
    "west_middle": {"region": "Моноройская область", "depth": "middle", "direction": "запад", "places": ["Моноройск", "Гера", "Наржа", "Зеленостопль"]},
    "northwest_middle": {"region": "Сугданская область", "depth": "middle", "direction": "северо-запад", "places": ["Озерослав", "Ромашка", "Рекаль"]},
    "north_middle": {"region": "Ангераская область", "depth": "middle", "direction": "север", "places": ["Ангерас", "Доковы", "Доброгород"]},

    "center_rear": {"region": "Озерославская область", "depth": "rear", "direction": "центр", "places": ["Озерославск", "Алержа"]},
    "kurb_rear": {"region": "Курбская область", "depth": "rear", "direction": "центр", "places": ["Курбск", "Дель", "Обищина", "Зелен"]},
    "verh_rear": {"region": "Верходиямская область", "depth": "rear", "direction": "центр", "places": ["Верходияма", "Дияга"]},
    "east_rear": {"region": "Ангераская область", "depth": "rear", "direction": "восток", "places": ["Ебаз", "Шенматор", "Кельматор"]},

    "diyam_region": {"region": "Диямская область", "depth": "rear", "direction": "восток", "places": ["Великий", "Фердель", "Оробож", "Нелян"]},
    "diyam_agglomeration": {"region": "Диямская агломерация", "depth": "rear", "direction": "восток", "places": ["Дияма", "Рейла", "Пуснарь", "Зелемай", "Хладский"]},

    "danel_far": {"region": "Дамельская область", "depth": "far", "direction": "восток", "places": ["Дамель", "Гамельск", "Гемель", "Душинка", "Смертный", "Нельск", "Дервей"]},
    "nel_far": {"region": "Курбская область, Нельский округ", "depth": "far", "direction": "восток", "places": ["Нель-Восточный", "Фруктовск", "Краин", "Курбанска"]},
}

THREAT_BY_DEPTH = {
    "close": ["artillery", "aviation", "ballistic", "missile", "fpv", "bpla"],
    "middle": ["artillery", "aviation", "ballistic", "missile", "bpla"],
    "rear": ["aviation", "ballistic", "missile", "bpla"],
    "far": ["aviation", "ballistic", "missile"],
}

SCENARIO_ALLOWED = {
    "mixed": ["artillery", "aviation", "ballistic", "missile", "fpv", "bpla"],
    "bpla": ["bpla"],
    "missile": ["missile", "ballistic"],
    "ballistic": ["ballistic"],
    "aviation": ["aviation", "missile", "ballistic"],
    "artillery": ["artillery"],
}

MODE_SETTINGS = {
    "calm": {"update_weight": 0.55, "clear_chance": 0.50, "expand_chance": 0.10, "combine_chance": 0.04},
    "normal": {"update_weight": 0.50, "clear_chance": 0.30, "expand_chance": 0.22, "combine_chance": 0.10},
    "hot": {"update_weight": 0.52, "clear_chance": 0.18, "expand_chance": 0.34, "combine_chance": 0.18},
    "chaos": {"update_weight": 0.58, "clear_chance": 0.12, "expand_chance": 0.42, "combine_chance": 0.28},
}

# БПЛА и FPV специально редкие. Баллистика часто встречается в mixed.
THREAT_WEIGHTS_BY_MODE = {
    "calm": {"bpla": 1, "fpv": 1, "artillery": 5, "aviation": 6, "missile": 5, "ballistic": 6},
    "normal": {"bpla": 1, "fpv": 1, "artillery": 6, "aviation": 7, "missile": 6, "ballistic": 8},
    "hot": {"bpla": 1, "fpv": 1, "artillery": 7, "aviation": 8, "missile": 7, "ballistic": 9},
    "chaos": {"bpla": 1, "fpv": 2, "artillery": 8, "aviation": 9, "missile": 8, "ballistic": 10},
}

DIRECTIONS_TEXT = {
    "юго-запад": ["с юго-западного направления", "по юго-западной дуге"],
    "запад": ["с западного направления", "по западной дуге"],
    "северо-запад": ["с северо-западного направления", "по северо-западной дуге"],
    "север": ["с северного направления", "по северной дуге"],
    "центр": ["в центральной части", "по центральному поясу"],
    "восток": ["на восточном направлении", "по восточной линии"],
}
